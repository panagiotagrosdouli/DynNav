#include "dynnav_nav2_cpp/dynnav_global_planner.hpp"

#include "pluginlib/class_list_macros.hpp"

namespace dynnav_nav2_cpp
{

void DynNavGlobalPlanner::configure(
  const rclcpp_lifecycle::LifecycleNode::WeakPtr & parent,
  std::string name,
  std::shared_ptr<tf2_ros::Buffer> tf,
  std::shared_ptr<nav2_costmap_2d::Costmap2DROS> costmap_ros)
{
  parent_ = parent;
  name_ = name;
  tf_ = tf;
  costmap_ros_ = costmap_ros;
}

void DynNavGlobalPlanner::cleanup()
{
}

void DynNavGlobalPlanner::activate()
{
}

void DynNavGlobalPlanner::deactivate()
{
}

nav_msgs::msg::Path DynNavGlobalPlanner::createPlan(
  const geometry_msgs::msg::PoseStamped & start,
  const geometry_msgs::msg::PoseStamped & goal)
{
  nav_msgs::msg::Path path;
  path.header = goal.header;
  path.poses.push_back(start);
  path.poses.push_back(goal);
  return path;
}

}  // namespace dynnav_nav2_cpp

PLUGINLIB_EXPORT_CLASS(dynnav_nav2_cpp::DynNavGlobalPlanner, nav2_core::GlobalPlanner)
