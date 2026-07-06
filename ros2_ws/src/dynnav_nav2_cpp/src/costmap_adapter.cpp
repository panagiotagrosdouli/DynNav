#include "dynnav_nav2_cpp/costmap_adapter.hpp"

#include <algorithm>

namespace dynnav_nav2_cpp
{

namespace
{
constexpr unsigned char kUnknownCost = 255;
constexpr unsigned char kInscribedCost = 253;
}  // namespace

double costToRisk(unsigned char cost)
{
  if (cost == kUnknownCost) {
    return 0.5;
  }
  return std::clamp(static_cast<double>(cost) / static_cast<double>(kInscribedCost), 0.0, 1.0);
}

double costToUncertainty(unsigned char cost)
{
  return cost == kUnknownCost ? 1.0 : 0.0;
}

bool isOccupiedCost(unsigned char cost, unsigned char lethal_threshold)
{
  if (cost == kUnknownCost) {
    return false;
  }
  return cost >= lethal_threshold;
}

GridCell indexToCell(unsigned int index, unsigned int width)
{
  return GridCell{index % width, index / width};
}

}  // namespace dynnav_nav2_cpp
