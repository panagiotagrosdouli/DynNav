#include "dynnav_nav2_cpp/history_grid_search.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <queue>
#include <stdexcept>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

namespace dynnav_nav2_cpp
{
namespace
{

constexpr double kEpsilon = 1.0e-12;

bool traversable(const std::uint8_t cost, const HistorySearchConfig & config)
{
  if (cost == config.unknown_cost) {
    return config.allow_unknown;
  }
  return cost < config.lethal_cost_threshold;
}

std::vector<std::size_t> neighbours4(
  const std::size_t index,
  const std::size_t width,
  const std::size_t height)
{
  const auto x = index % width;
  const auto y = index / width;
  std::vector<std::size_t> result;
  result.reserve(4);
  if (x + 1 < width) {result.push_back(index + 1);}
  if (x > 0) {result.push_back(index - 1);}
  if (y + 1 < height) {result.push_back(index + width);}
  if (y > 0) {result.push_back(index - width);}
  return result;
}

std::size_t manhattan(
  const std::size_t left,
  const std::size_t right,
  const std::size_t width)
{
  const auto lx = left % width;
  const auto ly = left / width;
  const auto rx = right % width;
  const auto ry = right / width;
  return (lx > rx ? lx - rx : rx - lx) + (ly > ry ? ly - ry : ry - ly);
}

std::uint64_t key(const std::size_t index, const std::uint64_t active_mask)
{
  if (index > std::numeric_limits<std::uint32_t>::max()) {
    throw std::invalid_argument("grid index exceeds history-state key capacity");
  }
  return (active_mask << 32U) | static_cast<std::uint64_t>(index);
}

std::size_t keyIndex(const std::uint64_t value)
{
  return static_cast<std::size_t>(value & 0xffffffffULL);
}

std::uint64_t keyMask(const std::uint64_t value)
{
  return value >> 32U;
}

bool reachesSafe(
  const std::size_t width,
  const std::size_t height,
  const std::vector<std::uint8_t> & costs,
  const std::size_t current,
  const std::unordered_set<std::size_t> & safe,
  const std::unordered_set<std::size_t> & closed,
  const HistorySearchConfig & config)
{
  if (safe.count(current) > 0U) {
    return true;
  }
  std::queue<std::size_t> frontier;
  std::vector<bool> visited(costs.size(), false);
  frontier.push(current);
  visited[current] = true;
  while (!frontier.empty()) {
    const auto cell = frontier.front();
    frontier.pop();
    for (const auto next : neighbours4(cell, width, height)) {
      if (visited[next] || closed.count(next) > 0U || !traversable(costs[next], config)) {
        continue;
      }
      if (safe.count(next) > 0U) {
        return true;
      }
      visited[next] = true;
      frontier.push(next);
    }
  }
  return false;
}

std::vector<bool> cellsReachingSafe(
  const std::size_t width,
  const std::size_t height,
  const std::vector<std::uint8_t> & costs,
  const std::vector<std::size_t> & safe_indices,
  const std::unordered_set<std::size_t> & closed,
  const HistorySearchConfig & config)
{
  std::queue<std::size_t> frontier;
  std::vector<bool> reachable(costs.size(), false);
  for (const auto safe : safe_indices) {
    if (safe >= costs.size() || closed.count(safe) > 0U || !traversable(costs[safe], config)) {
      continue;
    }
    if (!reachable[safe]) {
      reachable[safe] = true;
      frontier.push(safe);
    }
  }
  while (!frontier.empty()) {
    const auto cell = frontier.front();
    frontier.pop();
    for (const auto next : neighbours4(cell, width, height)) {
      if (reachable[next] || closed.count(next) > 0U || !traversable(costs[next], config)) {
        continue;
      }
      reachable[next] = true;
      frontier.push(next);
    }
  }
  return reachable;
}

std::uint64_t activatedAfter(
  const std::size_t source,
  const std::size_t target,
  const std::vector<HistoryHazard> & hazards,
  std::uint64_t mask)
{
  for (std::size_t i = 0; i < hazards.size(); ++i) {
    if (hazards[i].source_index == source && hazards[i].target_index == target) {
      mask |= (1ULL << i);
    }
  }
  return mask;
}

struct QueueEntry
{
  double priority{0.0};
  double cost{0.0};
  std::uint64_t state_key{0};
  std::size_t order{0};
};

struct GreaterPriority
{
  bool operator()(const QueueEntry & left, const QueueEntry & right) const
  {
    if (std::abs(left.priority - right.priority) > kEpsilon) {
      return left.priority > right.priority;
    }
    return left.order > right.order;
  }
};

}  // namespace

void validateHistorySearchInputs(
  const std::size_t width,
  const std::size_t height,
  const std::vector<std::uint8_t> & costs,
  const std::vector<std::size_t> & safe_indices,
  const std::vector<HistoryHazard> & hazards,
  const HistorySearchConfig & config)
{
  if (width == 0 || height == 0 || costs.size() != width * height) {
    throw std::invalid_argument("grid dimensions do not match the cost array");
  }
  if (config.lethal_cost_threshold == 0 || config.lethal_cost_threshold >= config.unknown_cost) {
    throw std::invalid_argument("lethal_cost_threshold must be in [1, unknown_cost)");
  }
  if (!std::isfinite(config.neutral_cost) || config.neutral_cost <= 0.0) {
    throw std::invalid_argument("neutral_cost must be finite and positive");
  }
  if (!std::isfinite(config.recoverability_weight) || config.recoverability_weight < 0.0) {
    throw std::invalid_argument("recoverability_weight must be finite and non-negative");
  }
  if (hazards.size() > config.max_hazard_cells || hazards.size() > 31U) {
    throw std::invalid_argument("history hazard count exceeds configured exact-search limit");
  }
  if (safe_indices.empty()) {
    throw std::invalid_argument("at least one safe cell is required");
  }
  for (const auto safe : safe_indices) {
    if (safe >= costs.size()) {throw std::out_of_range("safe cell is outside the grid");}
  }
  std::unordered_set<std::uint64_t> triggers;
  for (const auto & hazard : hazards) {
    if (hazard.source_index >= costs.size() || hazard.target_index >= costs.size() ||
      hazard.closure_index >= costs.size())
    {
      throw std::out_of_range("history hazard index is outside the grid");
    }
    if (manhattan(hazard.source_index, hazard.target_index, width) != 1U) {
      throw std::invalid_argument("history hazard trigger must be a 4-connected edge");
    }
    if (!std::isfinite(hazard.closure_probability) || hazard.closure_probability < 0.0 ||
      hazard.closure_probability > 1.0)
    {
      throw std::invalid_argument("closure probability must be in [0, 1]");
    }
    const auto trigger_key =
      (static_cast<std::uint64_t>(hazard.source_index) << 32U) |
      static_cast<std::uint64_t>(hazard.target_index);
    if (!triggers.insert(trigger_key).second) {
      throw std::invalid_argument("duplicate history hazard trigger");
    }
  }
}

double exactHistoryReturnProbability(
  const std::size_t width,
  const std::size_t height,
  const std::vector<std::uint8_t> & costs,
  const std::size_t current_index,
  const std::vector<std::size_t> & safe_indices,
  const std::vector<HistoryHazard> & hazards,
  const std::uint64_t active_mask,
  const HistorySearchConfig & config)
{
  validateHistorySearchInputs(width, height, costs, safe_indices, hazards, config);
  if (current_index >= costs.size()) {throw std::out_of_range("current cell is outside the grid");}
  if (active_mask >> hazards.size()) {
    throw std::invalid_argument("active hazard mask references an unknown hazard");
  }

  std::vector<std::size_t> active_indices;
  for (std::size_t i = 0; i < hazards.size(); ++i) {
    if ((active_mask & (1ULL << i)) != 0U) {active_indices.push_back(i);}
  }
  std::unordered_set<std::size_t> safe(safe_indices.begin(), safe_indices.end());
  if (active_indices.empty()) {
    return reachesSafe(width, height, costs, current_index, safe, {}, config) ? 1.0 : 0.0;
  }
  const std::uint64_t realization_count = 1ULL << active_indices.size();
  double probability = 0.0;
  for (std::uint64_t realization = 0; realization < realization_count; ++realization) {
    double mass = 1.0;
    std::unordered_set<std::size_t> closed;
    for (std::size_t bit = 0; bit < active_indices.size(); ++bit) {
      const auto & hazard = hazards[active_indices[bit]];
      const bool closes = (realization & (1ULL << bit)) != 0U;
      mass *= closes ? hazard.closure_probability : (1.0 - hazard.closure_probability);
      if (closes && hazard.closure_index != current_index) {
        closed.insert(hazard.closure_index);
      }
    }
    if (mass <= 0.0) {continue;}
    if (reachesSafe(width, height, costs, current_index, safe, closed, config)) {
      probability += mass;
    }
  }
  return probability;
}

HistorySearchResult planHistoryGridPath(
  const std::size_t width,
  const std::size_t height,
  const std::vector<std::uint8_t> & costs,
  const std::size_t start_index,
  const std::size_t goal_index,
  const std::vector<std::size_t> & safe_indices,
  const std::vector<HistoryHazard> & hazards,
  const std::uint64_t initial_active_mask,
  const HistorySearchConfig & config,
  const std::function<bool()> & cancel_checker)
{
  validateHistorySearchInputs(width, height, costs, safe_indices, hazards, config);
  if (start_index >= costs.size() || goal_index >= costs.size()) {
    throw std::out_of_range("start or goal index is outside the grid");
  }
  if (initial_active_mask >> hazards.size()) {
    throw std::invalid_argument("initial active mask references an unknown hazard");
  }

  HistorySearchResult result;
  if (!traversable(costs[start_index], config) || !traversable(costs[goal_index], config)) {
    return result;
  }

  const auto initial_key = key(start_index, initial_active_mask);

  // Exact fast path for the common zero/one-active-hazard case.  Reachability
  // is precomputed once per closure realization instead of running a graph
  // search for every A* successor.  Multi-hazard states retain the generic
  // exact enumerator below.
  const std::unordered_set<std::size_t> no_closed;
  const auto base_reachable =
    cellsReachingSafe(width, height, costs, safe_indices, no_closed, config);
  std::vector<std::vector<bool>> single_closed_reachable;
  single_closed_reachable.reserve(hazards.size());
  for (const auto & hazard : hazards) {
    single_closed_reachable.push_back(
      cellsReachingSafe(
        width,
        height,
        costs,
        safe_indices,
        std::unordered_set<std::size_t>{hazard.closure_index},
        config));
  }
  std::unordered_map<std::uint64_t, double> return_probability_cache;
  const auto returnProbability = [&](const std::size_t cell, const std::uint64_t mask) {
      const auto state_key = key(cell, mask);
      const auto cached = return_probability_cache.find(state_key);
      if (cached != return_probability_cache.end()) {
        return cached->second;
      }

      double probability = 0.0;
      if (mask == 0U) {
        probability = base_reachable[cell] ? 1.0 : 0.0;
      } else if ((mask & (mask - 1U)) == 0U) {
        std::size_t hazard_index = 0U;
        while ((mask & (1ULL << hazard_index)) == 0U) {
          ++hazard_index;
        }
        const auto & hazard = hazards[hazard_index];
        if (hazard.closure_index == cell) {
          probability = base_reachable[cell] ? 1.0 : 0.0;
        } else {
          const double open_probability = base_reachable[cell] ? 1.0 : 0.0;
          const double closed_probability =
            single_closed_reachable[hazard_index][cell] ? 1.0 : 0.0;
          probability =
            (1.0 - hazard.closure_probability) * open_probability +
            hazard.closure_probability * closed_probability;
        }
      } else {
        probability = exactHistoryReturnProbability(
          width, height, costs, cell, safe_indices, hazards, mask, config);
      }
      return_probability_cache.emplace(state_key, probability);
      return probability;
    };

  std::unordered_map<std::uint64_t, double> cost_so_far{{initial_key, 0.0}};
  std::unordered_map<std::uint64_t, std::uint64_t> parent;
  std::priority_queue<QueueEntry, std::vector<QueueEntry>, GreaterPriority> frontier;
  std::size_t order = 0;
  frontier.push({
    config.neutral_cost * static_cast<double>(manhattan(start_index, goal_index, width)),
    0.0,
    initial_key,
    order});

  while (!frontier.empty()) {
    if (cancel_checker && cancel_checker()) {
      result.cancelled = true;
      return result;
    }
    const auto current = frontier.top();
    frontier.pop();
    const auto known = cost_so_far.find(current.state_key);
    if (known == cost_so_far.end() || current.cost > known->second + kEpsilon) {continue;}
    if (config.max_iterations > 0 && result.expanded_nodes >= config.max_iterations) {return result;}
    ++result.expanded_nodes;

    const auto cell = keyIndex(current.state_key);
    const auto mask = keyMask(current.state_key);
    if (cell == goal_index) {
      result.success = true;
      result.total_cost = known->second;
      result.final_active_mask = mask;
      std::vector<std::uint64_t> states{current.state_key};
      auto cursor = current.state_key;
      while (cursor != initial_key) {
        const auto parent_it = parent.find(cursor);
        if (parent_it == parent.end()) {return HistorySearchResult{};}
        cursor = parent_it->second;
        states.push_back(cursor);
      }
      std::reverse(states.begin(), states.end());
      result.minimum_return_probability = 1.0;
      for (const auto state : states) {
        result.path.push_back(keyIndex(state));
        const double r = returnProbability(keyIndex(state), keyMask(state));
        result.minimum_return_probability = std::min(result.minimum_return_probability, r);
      }
      result.final_return_probability = returnProbability(goal_index, mask);
      return result;
    }

    for (const auto next : neighbours4(cell, width, height)) {
      if (!traversable(costs[next], config)) {continue;}
      const auto next_mask = activatedAfter(cell, next, hazards, mask);
      const double return_probability = returnProbability(next, next_mask);
      const double transition_cost =
        config.neutral_cost + config.recoverability_weight * (1.0 - return_probability);
      const double candidate = known->second + transition_cost;
      const auto next_key = key(next, next_mask);
      const auto next_known = cost_so_far.find(next_key);
      if (next_known == cost_so_far.end() || candidate + kEpsilon < next_known->second) {
        cost_so_far[next_key] = candidate;
        parent[next_key] = current.state_key;
        ++order;
        frontier.push({
          candidate + config.neutral_cost * static_cast<double>(manhattan(next, goal_index, width)),
          candidate,
          next_key,
          order});
      }
    }
  }
  return result;
}

}  // namespace dynnav_nav2_cpp
