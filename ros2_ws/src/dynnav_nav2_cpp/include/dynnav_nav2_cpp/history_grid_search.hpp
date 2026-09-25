#ifndef DYNNAV_NAV2_CPP__HISTORY_GRID_SEARCH_HPP_
#define DYNNAV_NAV2_CPP__HISTORY_GRID_SEARCH_HPP_

#include <cstddef>
#include <cstdint>
#include <functional>
#include <vector>

namespace dynnav_nav2_cpp
{

struct HistoryHazard
{
  std::size_t source_index{0};
  std::size_t target_index{0};
  std::size_t closure_index{0};
  double closure_probability{0.0};
};

struct HistorySearchConfig
{
  bool allow_unknown{true};
  std::uint8_t lethal_cost_threshold{253};
  std::uint8_t unknown_cost{255};
  double neutral_cost{1.0};
  double recoverability_weight{4.0};
  bool robust_pairwise_dependence{false};
  double pairwise_joint_lower{0.0};
  double pairwise_joint_upper{1.0};
  std::size_t max_hazard_cells{16};
  std::size_t max_iterations{0};
};

struct HistorySearchResult
{
  bool success{false};
  bool cancelled{false};
  std::vector<std::size_t> path;
  std::size_t expanded_nodes{0};
  double total_cost{0.0};
  double final_return_probability{0.0};
  double minimum_return_probability{0.0};
  std::uint64_t final_active_mask{0};
};

void validateHistorySearchInputs(
  std::size_t width,
  std::size_t height,
  const std::vector<std::uint8_t> & costs,
  const std::vector<std::size_t> & safe_indices,
  const std::vector<HistoryHazard> & hazards,
  const HistorySearchConfig & config);

double exactHistoryReturnProbability(
  std::size_t width,
  std::size_t height,
  const std::vector<std::uint8_t> & costs,
  std::size_t current_index,
  const std::vector<std::size_t> & safe_indices,
  const std::vector<HistoryHazard> & hazards,
  std::uint64_t active_mask,
  const HistorySearchConfig & config);

double robustPairwiseHistoryReturnProbability(
  std::size_t width,
  std::size_t height,
  const std::vector<std::uint8_t> & costs,
  std::size_t current_index,
  const std::vector<std::size_t> & safe_indices,
  const std::vector<HistoryHazard> & hazards,
  std::uint64_t active_mask,
  const HistorySearchConfig & config);

HistorySearchResult planHistoryGridPath(
  std::size_t width,
  std::size_t height,
  const std::vector<std::uint8_t> & costs,
  std::size_t start_index,
  std::size_t goal_index,
  const std::vector<std::size_t> & safe_indices,
  const std::vector<HistoryHazard> & hazards,
  std::uint64_t initial_active_mask,
  const HistorySearchConfig & config,
  const std::function<bool()> & cancel_checker = []() {return false;});

}  // namespace dynnav_nav2_cpp

#endif  // DYNNAV_NAV2_CPP__HISTORY_GRID_SEARCH_HPP_
