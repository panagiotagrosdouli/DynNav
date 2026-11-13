#include <memory>
#include <string>

#include "dynnav_nav2_cpp/dynnav_global_planner.hpp"
#include "gtest/gtest.h"
#include "nav2_core/planner_exceptions.hpp"

namespace dynnav_nav2_cpp
{
// Exercise actual callback and createPlan code against a real Costmap2D.
// This fixture bypasses ROS subscriptions; it is not a DDS/end-to-end trial.
struct PlannerTestAccess
{
  static void setup(DynNavGlobalPlanner & p, nav2_costmap_2d::Costmap2D & map)
  {
    p.costmap_ = &map;
    p.clock_ = std::make_shared<rclcpp::Clock>(RCL_SYSTEM_TIME);
    p.global_frame_ = "map";
    p.history_aware_ = true;
    p.history_width_ = map.getSizeInCellsX();
    p.history_height_ = map.getSizeInCellsY();
    p.history_resolution_ = map.getResolution();
    p.history_origin_x_ = map.getOriginX();
    p.history_origin_y_ = map.getOriginY();
    p.history_safe_indices_ = {0};
    p.history_hazards_ = {{1, 2, 1, 0.8}};
  }
  static std::uint64_t mask(const DynNavGlobalPlanner & p) {return p.active_history_mask_;}
  static void shortest(DynNavGlobalPlanner & p) {p.history_aware_ = false;}
  static std::string stamp(const DynNavGlobalPlanner & p)
  {
    return std::to_string(p.clock_->now().nanoseconds());
  }
  static void observe(DynNavGlobalPlanner & p, const std::string & text)
  {
    auto message = std::make_shared<std_msgs::msg::String>();
    message->data = text;
    p.onExecutedTransition(message);
  }
};

TEST(PlannerObservations, OnlyFreshFramedExecutedEventsActivatePersistentHistory)
{
  nav2_costmap_2d::Costmap2D map(6, 1, 1.0, 0.0, 0.0, 0);
  DynNavGlobalPlanner planner;
  PlannerTestAccess::setup(planner, map);
  const auto stamp = PlannerTestAccess::stamp(planner);
  for (const auto & text : {std::string("1:0>2:0"), "v1|odom|" + stamp + "|1:0>2:0",
      std::string("v1|map|1|1:0>2:0"), "v1|map|" + stamp + "|1:0>2:0junk"})
  {
    PlannerTestAccess::observe(planner, text);
    EXPECT_EQ(PlannerTestAccess::mask(planner), 0U);
  }
  geometry_msgs::msg::PoseStamped start, goal;
  start.header.frame_id = goal.header.frame_id = "map";
  start.pose.position.x = 1.5;
  start.pose.position.y = goal.pose.position.y = 0.5;
  goal.pose.position.x = 4.5;
  start.pose.orientation.w = goal.pose.orientation.w = 1.0;
  EXPECT_FALSE(planner.createPlan(start, goal, [] {return false;}).poses.empty());
  EXPECT_EQ(PlannerTestAccess::mask(planner), 0U);  // Planned triggers do not persist.
  PlannerTestAccess::observe(planner, "v1|map|" + PlannerTestAccess::stamp(planner) + "|1:0>2:0");
  EXPECT_EQ(PlannerTestAccess::mask(planner), 1U);
  EXPECT_FALSE(planner.createPlan(start, goal, [] {return false;}).poses.empty());
  EXPECT_EQ(PlannerTestAccess::mask(planner), 1U);  // Replanning cannot erase execution.
}

TEST(PlannerObservations, RejectsResizedOrShiftedHistoryCostmapWithoutClearingHazards)
{
  nav2_costmap_2d::Costmap2D map(6, 1, 1.0, 0.0, 0.0, 0);
  DynNavGlobalPlanner planner;
  PlannerTestAccess::setup(planner, map);
  PlannerTestAccess::observe(planner, "v1|map|" + PlannerTestAccess::stamp(planner) + "|1:0>2:0");
  map.resizeMap(12, 1, 1.0, 0.0, 0.0);
  geometry_msgs::msg::PoseStamped pose;
  pose.header.frame_id = "map";
  EXPECT_THROW(planner.createPlan(pose, pose, [] {return false;}), nav2_core::PlannerException);
  EXPECT_EQ(PlannerTestAccess::mask(planner), 1U);
}

TEST(PlannerObservations, PathCoordinatesUseTheSnapshotEvenIfMapChangesDuringSearch)
{
  nav2_costmap_2d::Costmap2D map(6, 1, 1.0, 0.0, 0.0, 0);
  DynNavGlobalPlanner planner;
  PlannerTestAccess::setup(planner, map);
  PlannerTestAccess::shortest(planner);
  geometry_msgs::msg::PoseStamped start, goal;
  start.header.frame_id = goal.header.frame_id = "map";
  start.pose.position.x = 0.5;
  goal.pose.position.x = 5.5;
  start.pose.position.y = goal.pose.position.y = 0.5;
  start.pose.orientation.w = goal.pose.orientation.w = 1.0;
  bool resized = false;
  const auto path = planner.createPlan(start, goal, [&]() {
      if (!resized) {
        map.resizeMap(12, 2, 2.0, 10.0, 20.0);
        resized = true;
      }
      return false;
    });
  EXPECT_TRUE(resized);
  ASSERT_EQ(path.poses.size(), 6U);
  EXPECT_DOUBLE_EQ(path.poses[2].pose.position.x, 2.5);
  EXPECT_DOUBLE_EQ(path.poses[2].pose.position.y, 0.5);
}
}  // namespace dynnav_nav2_cpp
