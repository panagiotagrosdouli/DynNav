#ifndef DYNNAV_NAV2_CPP__HISTORY_OBSERVATION_HPP_
#define DYNNAV_NAV2_CPP__HISTORY_OBSERVATION_HPP_

#include <algorithm>
#include <cstdint>
#include <limits>
#include <stdexcept>
#include <string>
#include <utility>

namespace dynnav_nav2_cpp
{
using HistoryCell = std::pair<unsigned int, unsigned int>;
using HistoryTransition = std::pair<HistoryCell, HistoryCell>;

inline std::uint64_t parseUnsigned(const std::string & text)
{
  if (text.empty()) {throw std::invalid_argument("empty unsigned integer");}
  std::uint64_t value = 0;
  for (const char c : text) {
    if (c < '0' || c > '9') {throw std::invalid_argument("unsigned integer must contain digits only");}
    const auto digit = static_cast<unsigned int>(c - '0');
    if (value > (std::numeric_limits<std::uint64_t>::max() - digit) / 10U) {
      throw std::out_of_range("unsigned integer overflow");
    }
    value = value * 10U + digit;
  }
  return value;
}

inline HistoryCell parseCell(const std::string & text)
{
  const auto sep = text.find(':');
  if (sep == std::string::npos || text.find(':', sep + 1) != std::string::npos) {
    throw std::invalid_argument("cell must be encoded as x:y");
  }
  const auto x = parseUnsigned(text.substr(0, sep));
  const auto y = parseUnsigned(text.substr(sep + 1));
  if (x > std::numeric_limits<unsigned int>::max() || y > std::numeric_limits<unsigned int>::max()) {
    throw std::out_of_range("cell coordinate overflow");
  }
  return {static_cast<unsigned int>(x), static_cast<unsigned int>(y)};
}

inline HistoryTransition parseTransition(const std::string & text)
{
  const auto sep = text.find('>');
  if (sep == std::string::npos || text.find('>', sep + 1) != std::string::npos) {
    throw std::invalid_argument("transition must be encoded as x:y>x:y");
  }
  return {parseCell(text.substr(0, sep)), parseCell(text.substr(sep + 1))};
}

inline bool adjacentTransition(const HistoryTransition & transition)
{
  const auto a = transition.first;
  const auto b = transition.second;
  const auto dx = std::max(a.first, b.first) - std::min(a.first, b.first);
  const auto dy = std::max(a.second, b.second) - std::min(a.second, b.second);
  return static_cast<std::uint64_t>(dx) + dy == 1U;
}

struct StampedTransition
{
  std::uint64_t stamp_ns;
  HistoryTransition transition;
};

inline StampedTransition parseObservation(
  const std::string & text, const std::string & frame, const std::uint64_t now_ns,
  const std::uint64_t previous_ns = 0U)
{
  // Explicit wire contract: v1|global_frame|measurement_stamp_ns|sx:sy>tx:ty.
  // Same ROS clock domain as the planner; no wall-time substitution is allowed.
  const auto a = text.find('|');
  const auto b = a == std::string::npos ? a : text.find('|', a + 1);
  const auto c = b == std::string::npos ? b : text.find('|', b + 1);
  if (a == std::string::npos || b == std::string::npos || c == std::string::npos ||
    text.find('|', c + 1) != std::string::npos || text.substr(0, a) != "v1" ||
    frame.empty() || text.substr(a + 1, b - a - 1) != frame)
  {
    throw std::invalid_argument("execution observation version/frame mismatch");
  }
  const auto stamp = parseUnsigned(text.substr(b + 1, c - b - 1));
  constexpr std::uint64_t max_age = 1500000000ULL;
  constexpr std::uint64_t future_tolerance = 50000000ULL;
  if (stamp == 0U || stamp <= previous_ns ||
    (stamp > now_ns && stamp - now_ns > future_tolerance) ||
    (now_ns >= stamp && now_ns - stamp > max_age))
  {
    throw std::invalid_argument("execution observation stale, future, zero or out of order");
  }
  const auto transition = parseTransition(text.substr(c + 1));
  if (!adjacentTransition(transition)) {
    throw std::invalid_argument("execution observation must be one adjacent transition");
  }
  return {stamp, transition};
}
}  // namespace dynnav_nav2_cpp
#endif  // DYNNAV_NAV2_CPP__HISTORY_OBSERVATION_HPP_
