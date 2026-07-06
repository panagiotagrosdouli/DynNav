#ifndef DYNNAV_NAV2_CPP__COSTMAP_ADAPTER_HPP_
#define DYNNAV_NAV2_CPP__COSTMAP_ADAPTER_HPP_

#include <cstdint>
#include <vector>

namespace dynnav_nav2_cpp
{

struct GridCell
{
  unsigned int x;
  unsigned int y;
};

struct DynNavCostCell
{
  GridCell cell;
  bool occupied;
  double risk;
  double uncertainty;
};

struct DynNavCostmapSnapshot
{
  unsigned int width;
  unsigned int height;
  double resolution;
  std::vector<DynNavCostCell> cells;
};

double costToRisk(unsigned char cost);
double costToUncertainty(unsigned char cost);
bool isOccupiedCost(unsigned char cost, unsigned char lethal_threshold);
GridCell indexToCell(unsigned int index, unsigned int width);

}  // namespace dynnav_nav2_cpp

#endif  // DYNNAV_NAV2_CPP__COSTMAP_ADAPTER_HPP_
