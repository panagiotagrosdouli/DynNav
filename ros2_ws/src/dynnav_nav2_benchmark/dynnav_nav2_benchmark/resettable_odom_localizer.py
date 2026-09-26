"""Resettable odometry-based map localization for controlled Gazebo studies.

The node publishes map->odom so the current odometry pose coincides with a
known frozen map start pose.  On the reserved DynNav history reset command it
recomputes the SE(2) offset from the latest odometry sample.

This is experiment infrastructure for simulator localization control.  It is
not a replacement for real-world localization.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry
import rclpy
from rclpy.node import Node
from std_msgs.msg import String, UInt64
from tf2_ros import TransformBroadcaster

from dynnav_nav2_benchmark.history_execution import HISTORY_RESET_COMMAND


@dataclass(frozen=True, slots=True)
class PlanarPose:
    x: float
    y: float
    yaw: float


def map_to_odom_alignment(
    *,
    desired_map_base: PlanarPose,
    current_odom_base: PlanarPose,
) -> PlanarPose:
    """Return map->odom transform making current odom/base equal desired map/base."""

    yaw = desired_map_base.yaw - current_odom_base.yaw
    cosine = math.cos(yaw)
    sine = math.sin(yaw)
    rotated_x = cosine * current_odom_base.x - sine * current_odom_base.y
    rotated_y = sine * current_odom_base.x + cosine * current_odom_base.y
    return PlanarPose(
        desired_map_base.x - rotated_x,
        desired_map_base.y - rotated_y,
        yaw,
    )


def apply_planar_transform(transform: PlanarPose, pose: PlanarPose) -> PlanarPose:
    """Compose a planar parent->child transform with a child-frame pose."""

    cosine = math.cos(transform.yaw)
    sine = math.sin(transform.yaw)
    return PlanarPose(
        transform.x + cosine * pose.x - sine * pose.y,
        transform.y + sine * pose.x + cosine * pose.y,
        transform.yaw + pose.yaw,
    )


def _yaw_from_odometry(message: Odometry) -> float:
    q = message.pose.pose.orientation
    return math.atan2(
        2.0 * (q.w * q.z + q.x * q.y),
        1.0 - 2.0 * (q.y * q.y + q.z * q.z),
    )


class ResettableOdomLocalizer(Node):
    def __init__(self) -> None:
        super().__init__("dynnav_resettable_odom_localizer")

        self.declare_parameter("start_x", 0.0)
        self.declare_parameter("start_y", 0.0)
        self.declare_parameter("start_yaw", 0.0)
        self.declare_parameter("map_frame", "map")
        self.declare_parameter("odom_frame", "odom")
        self.declare_parameter("odom_topic", "odom")
        self.declare_parameter("reset_topic", "dynnav/executed_transition")

        self._desired_start = PlanarPose(
            float(self.get_parameter("start_x").value),
            float(self.get_parameter("start_y").value),
            float(self.get_parameter("start_yaw").value),
        )
        self._map_frame = str(self.get_parameter("map_frame").value)
        self._odom_frame = str(self.get_parameter("odom_frame").value)
        odom_topic = str(self.get_parameter("odom_topic").value)
        reset_topic = str(self.get_parameter("reset_topic").value)

        self._latest_odom: PlanarPose | None = None
        self._map_to_odom: PlanarPose | None = None
        self._reset_pending = False
        self._reset_count = 0
        self._broadcaster = TransformBroadcaster(self)
        self._ack_publisher = self.create_publisher(
            UInt64,
            "dynnav/localization_reset_epoch",
            20,
        )

        self.create_subscription(Odometry, odom_topic, self._on_odom, 50)
        self.create_subscription(String, reset_topic, self._on_reset, 20)

    def _on_odom(self, message: Odometry) -> None:
        current = PlanarPose(
            float(message.pose.pose.position.x),
            float(message.pose.pose.position.y),
            _yaw_from_odometry(message),
        )
        self._latest_odom = current

        was_pending = self._reset_pending
        if self._map_to_odom is None or self._reset_pending:
            self._realign()
        if was_pending and not self._reset_pending:
            self._reset_count += 1
            self._log_reset_alignment()
            self._publish_reset_ack()
        if self._map_to_odom is not None:
            self._broadcast(message)

    def _on_reset(self, message: String) -> None:
        if message.data != HISTORY_RESET_COMMAND:
            return
        if self._latest_odom is None:
            self._reset_pending = True
            self.get_logger().warning(
                "Received history reset before first odometry sample; alignment deferred"
            )
            return
        self._realign()
        self._reset_count += 1
        self._log_reset_alignment()
        self._publish_reset_ack()

    def _publish_reset_ack(self) -> None:
        self._ack_publisher.publish(UInt64(data=self._reset_count))

    def _realign(self) -> None:
        if self._latest_odom is None:
            self._reset_pending = True
            return
        self._map_to_odom = map_to_odom_alignment(
            desired_map_base=self._desired_start,
            current_odom_base=self._latest_odom,
        )
        self._reset_pending = False

    def _log_reset_alignment(self) -> None:
        assert self._map_to_odom is not None
        self.get_logger().info(
            "Aligned map->odom "
            f"reset={self._reset_count} "
            f"offset=({self._map_to_odom.x:.3f}, "
            f"{self._map_to_odom.y:.3f}, "
            f"{self._map_to_odom.yaw:.3f})"
        )

    def _broadcast(self, odometry: Odometry) -> None:
        assert self._map_to_odom is not None
        transform = TransformStamped()
        transform.header.stamp = odometry.header.stamp
        transform.header.frame_id = self._map_frame
        transform.child_frame_id = self._odom_frame
        transform.transform.translation.x = self._map_to_odom.x
        transform.transform.translation.y = self._map_to_odom.y
        transform.transform.translation.z = 0.0
        half = self._map_to_odom.yaw / 2.0
        transform.transform.rotation.z = math.sin(half)
        transform.transform.rotation.w = math.cos(half)
        self._broadcaster.sendTransform(transform)


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = ResettableOdomLocalizer()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
