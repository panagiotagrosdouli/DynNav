#ifndef DYNNAV_NAV2_CPP__DYNNAV_GLOBAL_PLANNER_HPP_
#define DYNNAV_NAV2_CPP__DYNNAV_GLOBAL_PLANNER_HPP_

#include <cstdint>
#include <functional>
#include <memory>
#include <mutex>
#include <string>
#include <vector>

#include "geometry_msgs/msg/pose_stamped.hpp"
#include "dynnav_nav2_cpp/grid_search.hpp"
#include "dynnav_nav2_cpp/history_grid_search.hpp"
#include "nav2_core/global_planner.hpp"
#include "nav2_costmap_2d/costmap_2d.hpp"
#include "nav2_costmap_2d/costmap_2d_ros.hpp"
#include "nav_msgs/msg/path.hpp"
#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"
#include "tf2_ros/buffer.h"

namespace dynnav_nav2_cpp
{

class DynNavGlobalPlanner : public nav2_core::GlobalPlanner
{
public:
  DynNavGlobalPlanner() = default;
  ~DynNavGlobalPlanner() override = default;

  void configure(
    const rclcpp_lifecycle::LifecycleNode::WeakPtr & parent,
    std::string name,
    std::shared_ptr<tf2_ros::Buffer> tf,
    std::shared_ptr<nav2_costmap_2d::Costmap2DROS> costmap_ros) override;

  void cleanup() override;
  void activate() override;
  void deactivate() override;

  nav_msgs::msg::Path createPlan(
    const geometry_msgs::msg::PoseStamped & start,
    const geometry_msgs::msg::PoseStamped & goal,
    std::function<bool()> cancel_checker) override;

private:
  void onExecutedTransition(const std_msgs::msg::String::SharedPtr message);

  rclcpp_lifecycle::LifecycleNode::WeakPtr node_;
  std::string name_;
  std::string global_frame_;
  std::shared_ptr<tf2_ros::Buffer> tf_;
  std::shared_ptr<nav2_costmap_2d::Costmap2DROS> costmap_ros_;
  nav2_costmap_2d::Costmap2D * costmap_{nullptr};
  rclcpp::Clock::SharedPtr clock_;
  rclcpp::Logger logger_{rclcpp::get_logger("dynnav_nav2_cpp")};
  GridSearchConfig search_config_;

  bool history_aware_{false};
  HistorySearchConfig history_config_;
  std::vector<HistoryHazard> history_hazards_;
  std::vector<std::size_t> history_safe_indices_;
  std::uint64_t active_history_mask_{0};
  bool observed_cell_valid_{false};
  std::size_t observed_cell_{0};
  std::mutex history_mutex_;
  rclcpp::Subscription<std_msgs::msg::String>::SharedPtr transition_subscription_;
};

}  // namespace dynnav_nav2_cpp

#endif  // DYNNAV_NAV2_CPP__DYNNAV_GLOBAL_PLANNER_HPP_
