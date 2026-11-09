"""C05 actual ROS 2 risk-to-safe-mode supervisor (planning/diagnostics ONLY).

Subscribes Float64 observations from /c05/risk_proxy and publishes String
policy diagnostics on /c05/mode_diagnostics. It never publishes /cmd_vel or
commands a real robot, and the scalar risk input is not a safety-certified
measurement. A stale feed fails closed to EMERGENCY_STOP.
"""
from __future__ import annotations
import argparse
import json
import math
import sys
import time
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"code"))
from safe_mode_controller import SafeModeController

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--timeout-seconds",type=float,default=2.0)
    a=p.parse_args()
    if not math.isfinite(a.timeout_seconds) or a.timeout_seconds<=0:
        p.error("timeout-seconds must be finite and positive")

    import rclpy
    from rclpy.node import Node
    from std_msgs.msg import Float64, String

    class Supervisor(Node):
        def __init__(self):
            super().__init__("c05_safe_mode_ros2_diagnostics_only")
            self.controller=SafeModeController()
            self.last_received=None
            self.stale_latched=False
            self.topic=self.create_subscription(Float64,"/c05/risk_proxy",self.on_risk,10)
            self.pub=self.create_publisher(String,"/c05/mode_diagnostics",10)
            self.timer=self.create_timer(.1,self.on_watchdog)

        def publish_output(self,out):
            msg=String()
            msg.data=json.dumps({
                **out.to_dict(),
                "evidence":"ACTUAL_ROS2_MIDDLEWARE_SCALAR_RISK_INPUT_NOT_HARDWARE_SAFETY",
                "physical_robot_trials":0,
                "physical_robot_movement":False,
                "actuation_commanded":False,
            },sort_keys=True)
            self.pub.publish(msg)

        def on_risk(self,msg):
            self.last_received=time.monotonic()
            self.stale_latched=False
            out=self.controller.update(msg.data)
            self.publish_output(out)

        def on_watchdog(self):
            if self.last_received is None:
                return
            if time.monotonic()-self.last_received>a.timeout_seconds and not self.stale_latched:
                # Nonfinite risk is consumed as a critical finite sentinel.
                self.stale_latched=True
                self.publish_output(self.controller.update(float("nan")))

    rclpy.init()
    node=Supervisor()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__=="__main__":
    main()
