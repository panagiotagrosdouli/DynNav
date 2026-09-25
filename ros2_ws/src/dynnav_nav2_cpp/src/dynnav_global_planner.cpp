#include "dynnav_nav2_cpp/dynnav_global_planner.hpp"

#include <cmath>
#include <cstdint>
#include <memory>
#include <mutex>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

#include "nav2_core/planner_exceptions.hpp"
#include "nav2_util/node_utils.hpp"
#include "pluginlib/class_list_macros.hpp"
#include "tf2/LinearMath/Quaternion.h"
#include "tf2_geometry_msgs/tf2_geometry_msgs.hpp"

namespace dynnav_nav2_cpp
{
namespace
{

std::vector<std::string> split(const std::string & text, const char delimiter)
{
  std::vector<std::string> parts;
  std::stringstream stream(text);
  std::string item;
  while (std::getline(stream, item, delimiter)) {
    if (!item.empty()) {
      parts.push_back(item);
    }
  }
  return parts;
}

std::pair<unsigned int, unsigned int> parseCell(const std::string & text)
{
  const auto parts = split(text, ':');
  if (parts.size() != 2U) {
    throw std::invalid_argument("cell must be encoded as x:y");
  }
  const auto x = std::stoul(parts[0]);
  const auto y = std::stoul(parts[1]);
  return {static_cast<unsigned int>(x), static_cast<unsigned int>(y)};
}

std::pair<std::pair<unsigned int, unsigned int>, std::pair<unsigned int, unsigned int>>
parseTransition(const std::string & text)
{
  const auto parts = split(text, '>');
  if (parts.size() != 2U) {
    throw std::invalid_argument("transition must be encoded as x:y>x:y");
  }
  return {parseCell(parts[0]), parseCell(parts[1])};
}

std::size_t checkedIndex(
  nav2_costmap_2d::Costmap2D * costmap,
  const std::pair<unsigned int, unsigned int> & cell)
{
  if (cell.first >= costmap->getSizeInCellsX() || cell.second >= costmap->getSizeInCellsY()) {
    throw std::out_of_range("history cell is outside the global costmap");
  }
  return static_cast<std::size_t>(costmap->getIndex(cell.first, cell.second));
}

std::vector<std::size_t> parseSafeCells(
  nav2_costmap_2d::Costmap2D * costmap,
  const std::string & raw)
{
  std::vector<std::size_t> result;
  for (const auto & item : split(raw, ',')) {
    result.push_back(checkedIndex(costmap, parseCell(item)));
  }
  return result;
}

std::vector<HistoryHazard> parseHistoryHazards(
  nav2_costmap_2d::Costmap2D * costmap,
  const std::string & raw)
{
  std::vector<HistoryHazard> result;
  for (const auto & item : split(raw, ';')) {
    const auto fields = split(item, '@');
    if (fields.size() != 3U) {
      throw std::invalid_argument(
              "history hazard must be trigger@closure@probability");
    }
    const auto trigger = parseTransition(fields[0]);
    const auto closure_parts = split(fields[1], '+');
    if (closure_parts.empty()) {
      throw std::invalid_argument("history hazard closure footprint cannot be empty");
    }
    std::vector<std::size_t> closure_indices;
    closure_indices.reserve(closure_parts.size());
    for (const auto & closure_part : closure_parts) {
      closure_indices.push_back(checkedIndex(costmap, parseCell(closure_part)));
    }
    result.push_back({
      checkedIndex(costmap, trigger.first),
      checkedIndex(costmap, trigger.second),
      closure_indices.front(),
      std::stod(fields[2]),
      std::move(closure_indices)});
  }
  return result;
}

}  // namespace

void DynNavGlobalPlanner::configure(
  const rclcpp_lifecycle::LifecycleNode::WeakPtr & parent,
  std::string name,
  std::shared_ptr<tf2_ros::Buffer> tf,
  std::shared_ptr<nav2_costmap_2d::Costmap2DROS> costmap_ros)
{
  node_ = parent;
  name_ = name;
  tf_ = std::move(tf);
  costmap_ros_ = std::move(costmap_ros);
  costmap_ = costmap_ros_->getCostmap();
  global_frame_ = costmap_ros_->getGlobalFrameID();

  const auto node = parent.lock();
  if (!node) {
    throw nav2_core::PlannerException("DynNav planner parent lifecycle node expired");
  }
  clock_ = node->get_clock();
  logger_ = node->get_logger();

  nav2_util::declare_parameter_if_not_declared(
    node, name_ + ".allow_unknown", rclcpp::ParameterValue(true));
  nav2_util::declare_parameter_if_not_declared(
    node, name_ + ".lethal_cost_threshold", rclcpp::ParameterValue(253));
  nav2_util::declare_parameter_if_not_declared(
    node, name_ + ".neutral_cost", rclcpp::ParameterValue(1.0));
  nav2_util::declare_parameter_if_not_declared(
    node, name_ + ".risk_weight", rclcpp::ParameterValue(4.0));
  nav2_util::declare_parameter_if_not_declared(
    node, name_ + ".irreversibility_weight", rclcpp::ParameterValue(4.0));
  nav2_util::declare_parameter_if_not_declared(
    node, name_ + ".unknown_risk", rclcpp::ParameterValue(0.5));
  nav2_util::declare_parameter_if_not_declared(
    node, name_ + ".max_iterations", rclcpp::ParameterValue(0));

  nav2_util::declare_parameter_if_not_declared(
    node, name_ + ".history_aware", rclcpp::ParameterValue(false));
  nav2_util::declare_parameter_if_not_declared(
    node, name_ + ".history_safe_cells", rclcpp::ParameterValue(std::string("")));
  nav2_util::declare_parameter_if_not_declared(
    node, name_ + ".history_hazards", rclcpp::ParameterValue(std::string("")));
  nav2_util::declare_parameter_if_not_declared(
    node, name_ + ".history_recoverability_weight", rclcpp::ParameterValue(4.0));
  nav2_util::declare_parameter_if_not_declared(
    node, name_ + ".history_robust_pairwise_dependence", rclcpp::ParameterValue(false));
  nav2_util::declare_parameter_if_not_declared(
    node, name_ + ".history_pairwise_joint_lower", rclcpp::ParameterValue(0.0));
  nav2_util::declare_parameter_if_not_declared(
    node, name_ + ".history_pairwise_joint_upper", rclcpp::ParameterValue(1.0));
  nav2_util::declare_parameter_if_not_declared(
    node, name_ + ".history_max_hazard_cells", rclcpp::ParameterValue(16));

  int lethal_cost_threshold = 253;
  int max_iterations = 0;
  node->get_parameter(name_ + ".allow_unknown", search_config_.allow_unknown);
  node->get_parameter(name_ + ".lethal_cost_threshold", lethal_cost_threshold);
  node->get_parameter(name_ + ".neutral_cost", search_config_.neutral_cost);
  node->get_parameter(name_ + ".risk_weight", search_config_.risk_weight);
  node->get_parameter(name_ + ".irreversibility_weight", search_config_.irreversibility_weight);
  node->get_parameter(name_ + ".unknown_risk", search_config_.unknown_risk);
  node->get_parameter(name_ + ".max_iterations", max_iterations);

  if (lethal_cost_threshold < 1 || lethal_cost_threshold > 254) {
    throw nav2_core::PlannerException("lethal_cost_threshold must be in [1, 254]");
  }
  if (max_iterations < 0) {
    throw nav2_core::PlannerException("max_iterations must be non-negative");
  }
  search_config_.lethal_cost_threshold = static_cast<std::uint8_t>(lethal_cost_threshold);
  search_config_.max_iterations = static_cast<std::size_t>(max_iterations);
  validateGridSearchConfig(search_config_);

  node->get_parameter(name_ + ".history_aware", history_aware_);
  if (history_aware_) {
    std::string safe_cells_raw;
    std::string hazards_raw;
    int history_max_hazard_cells = 16;
    node->get_parameter(name_ + ".history_safe_cells", safe_cells_raw);
    node->get_parameter(name_ + ".history_hazards", hazards_raw);
    node->get_parameter(
      name_ + ".history_recoverability_weight", history_config_.recoverability_weight);
    node->get_parameter(
      name_ + ".history_robust_pairwise_dependence",
      history_config_.robust_pairwise_dependence);
    node->get_parameter(
      name_ + ".history_pairwise_joint_lower", history_config_.pairwise_joint_lower);
    node->get_parameter(
      name_ + ".history_pairwise_joint_upper", history_config_.pairwise_joint_upper);
    node->get_parameter(name_ + ".history_max_hazard_cells", history_max_hazard_cells);
    if (history_max_hazard_cells < 0) {
      throw nav2_core::PlannerException("history_max_hazard_cells must be non-negative");
    }
    history_config_.allow_unknown = search_config_.allow_unknown;
    history_config_.lethal_cost_threshold = search_config_.lethal_cost_threshold;
    history_config_.unknown_cost = search_config_.unknown_cost;
    history_config_.neutral_cost = search_config_.neutral_cost;
    history_config_.max_iterations = search_config_.max_iterations;
    history_config_.max_hazard_cells = static_cast<std::size_t>(history_max_hazard_cells);
    try {
      history_safe_indices_ = parseSafeCells(costmap_, safe_cells_raw);
      history_hazards_ = parseHistoryHazards(costmap_, hazards_raw);
      if (history_safe_indices_.empty()) {
        throw std::invalid_argument("history_safe_cells cannot be empty in history-aware mode");
      }
      const auto width = static_cast<std::size_t>(costmap_->getSizeInCellsX());
      const auto height = static_cast<std::size_t>(costmap_->getSizeInCellsY());
      std::vector<std::uint8_t> empty_costs(width * height, 0U);
      validateHistorySearchInputs(
        width, height, empty_costs, history_safe_indices_, history_hazards_, history_config_);
    } catch (const std::exception & exc) {
      throw nav2_core::PlannerException(
              std::string("invalid history-aware configuration: ") + exc.what());
    }

    transition_subscription_ = node->create_subscription<std_msgs::msg::String>(
      "dynnav/executed_transition",
      rclcpp::QoS(50),
      std::bind(&DynNavGlobalPlanner::onExecutedTransition, this, std::placeholders::_1));
  }

  RCLCPP_INFO(
    logger_,
    "Configured %s: risk_weight=%.3f irreversibility_weight=%.3f allow_unknown=%s "
    "history_aware=%s robust_pairwise=%s",
    name_.c_str(), search_config_.risk_weight, search_config_.irreversibility_weight,
    search_config_.allow_unknown ? "true" : "false",
    history_aware_ ? "true" : "false",
    history_config_.robust_pairwise_dependence ? "true" : "false");
}

void DynNavGlobalPlanner::cleanup()
{
  RCLCPP_INFO(logger_, "Cleaning up DynNav planner %s", name_.c_str());
  transition_subscription_.reset();
  {
    std::lock_guard<std::mutex> lock(history_mutex_);
    active_history_mask_ = 0U;
    observed_cell_valid_ = false;
  }
  costmap_ = nullptr;
  costmap_ros_.reset();
  tf_.reset();
  clock_.reset();
}

void DynNavGlobalPlanner::activate()
{
  RCLCPP_INFO(logger_, "Activating DynNav planner %s", name_.c_str());
}

void DynNavGlobalPlanner::deactivate()
{
  RCLCPP_INFO(logger_, "Deactivating DynNav planner %s", name_.c_str());
}

void DynNavGlobalPlanner::onExecutedTransition(const std_msgs::msg::String::SharedPtr message)
{
  if (!history_aware_ || costmap_ == nullptr) {
    return;
  }
  try {
    const auto transition = parseTransition(message->data);
    const auto source = checkedIndex(costmap_, transition.first);
    const auto target = checkedIndex(costmap_, transition.second);
    std::lock_guard<std::mutex> lock(history_mutex_);
    if (observed_cell_valid_ && source != observed_cell_) {
      RCLCPP_ERROR(
        logger_,
        "Rejected out-of-order executed transition %s: source index %zu != observed %zu",
        message->data.c_str(), source, observed_cell_);
      return;
    }
    for (std::size_t i = 0; i < history_hazards_.size(); ++i) {
      if (history_hazards_[i].source_index == source &&
        history_hazards_[i].target_index == target)
      {
        active_history_mask_ |= (1ULL << i);
      }
    }
    observed_cell_ = target;
    observed_cell_valid_ = true;
  } catch (const std::exception & exc) {
    RCLCPP_ERROR(logger_, "Invalid executed transition '%s': %s", message->data.c_str(), exc.what());
  }
}

nav_msgs::msg::Path DynNavGlobalPlanner::createPlan(
  const geometry_msgs::msg::PoseStamped & start,
  const geometry_msgs::msg::PoseStamped & goal,
  std::function<bool()> cancel_checker)
{
  if (costmap_ == nullptr || clock_ == nullptr) {
    throw nav2_core::PlannerException("DynNav planner has not been configured");
  }
  if (start.header.frame_id != global_frame_ || goal.header.frame_id != global_frame_) {
    throw nav2_core::PlannerTFError(
            "Start and goal must be expressed in the global costmap frame " + global_frame_);
  }

  unsigned int start_x = 0;
  unsigned int start_y = 0;
  unsigned int goal_x = 0;
  unsigned int goal_y = 0;
  if (!costmap_->worldToMap(start.pose.position.x, start.pose.position.y, start_x, start_y)) {
    throw nav2_core::StartOutsideMapBounds("Start pose is outside the global costmap");
  }
  if (!costmap_->worldToMap(goal.pose.position.x, goal.pose.position.y, goal_x, goal_y)) {
    throw nav2_core::GoalOutsideMapBounds("Goal pose is outside the global costmap");
  }

  const auto width = static_cast<std::size_t>(costmap_->getSizeInCellsX());
  const auto height = static_cast<std::size_t>(costmap_->getSizeInCellsY());
  const auto start_index = static_cast<std::size_t>(costmap_->getIndex(start_x, start_y));
  const auto goal_index = static_cast<std::size_t>(costmap_->getIndex(goal_x, goal_y));

  std::vector<std::uint8_t> costs;
  {
    std::unique_lock<nav2_costmap_2d::Costmap2D::mutex_t> lock(*(costmap_->getMutex()));
    const auto * char_map = costmap_->getCharMap();
    costs.assign(char_map, char_map + width * height);
  }
  costs[start_index] = 0U;

  std::vector<std::size_t> planned_indices;
  std::size_t expanded_nodes = 0U;
  double objective = 0.0;
  if (history_aware_) {
    std::uint64_t active_mask = 0U;
    {
      std::lock_guard<std::mutex> lock(history_mutex_);
      if (observed_cell_valid_ && observed_cell_ != start_index) {
        RCLCPP_WARN(
          logger_,
          "Planner start index %zu differs from last executed-transition cell %zu; synchronizing position without clearing activated history",
          start_index, observed_cell_);
      }
      observed_cell_ = start_index;
      observed_cell_valid_ = true;
      active_mask = active_history_mask_;
    }

    const auto result = planHistoryGridPath(
      width,
      height,
      costs,
      start_index,
      goal_index,
      history_safe_indices_,
      history_hazards_,
      active_mask,
      history_config_,
      cancel_checker);
    if (result.cancelled) {
      throw nav2_core::PlannerCancelled("DynNav history-aware planning request was cancelled");
    }
    if (!result.success) {
      throw nav2_core::NoValidPathCouldBeFound(
              "DynNav history-aware planner could not find a traversable path");
    }
    planned_indices = result.path;
    expanded_nodes = result.expanded_nodes;
    objective = result.total_cost;
    RCLCPP_DEBUG(
      logger_,
      "History-aware path: active_mask=%llu projected_final_mask=%llu min_return=%.6f final_return=%.6f",
      static_cast<unsigned long long>(active_mask),
      static_cast<unsigned long long>(result.final_active_mask),
      result.minimum_return_probability,
      result.final_return_probability);
  } else {
    if (!isTraversable(costs[goal_index], search_config_)) {
      throw nav2_core::GoalOccupied("Goal cell is not traversable");
    }
    const auto result = planGridPath(
      width, height, costs, start_index, goal_index, search_config_, cancel_checker);
    if (result.cancelled) {
      throw nav2_core::PlannerCancelled("DynNav planning request was cancelled");
    }
    if (!result.success) {
      throw nav2_core::NoValidPathCouldBeFound("DynNav could not find a traversable path");
    }
    planned_indices = result.path;
    expanded_nodes = result.expanded_nodes;
    objective = result.total_cost;
  }

  nav_msgs::msg::Path path;
  path.header.stamp = clock_->now();
  path.header.frame_id = global_frame_;
  path.poses.reserve(planned_indices.size());

  for (const auto index : planned_indices) {
    const auto map_x = static_cast<unsigned int>(index % width);
    const auto map_y = static_cast<unsigned int>(index / width);
    double world_x = 0.0;
    double world_y = 0.0;
    costmap_->mapToWorld(map_x, map_y, world_x, world_y);

    geometry_msgs::msg::PoseStamped pose;
    pose.header = path.header;
    pose.pose.position.x = world_x;
    pose.pose.position.y = world_y;
    pose.pose.orientation.w = 1.0;
    path.poses.push_back(pose);
  }

  if (path.poses.empty()) {
    throw nav2_core::NoValidPathCouldBeFound("DynNav returned an empty successful path");
  }
  path.poses.front().pose.position = start.pose.position;
  path.poses.back().pose = goal.pose;
  for (std::size_t index = 0; index + 1 < path.poses.size(); ++index) {
    const auto & current = path.poses[index].pose.position;
    const auto & next = path.poses[index + 1].pose.position;
    tf2::Quaternion orientation;
    orientation.setRPY(0.0, 0.0, std::atan2(next.y - current.y, next.x - current.x));
    path.poses[index].pose.orientation = tf2::toMsg(orientation);
  }

  RCLCPP_DEBUG(
    logger_, "DynNav path: %zu poses, %zu expanded nodes, objective %.3f",
    path.poses.size(), expanded_nodes, objective);
  return path;
}

}  // namespace dynnav_nav2_cpp

PLUGINLIB_EXPORT_CLASS(dynnav_nav2_cpp::DynNavGlobalPlanner, nav2_core::GlobalPlanner)
