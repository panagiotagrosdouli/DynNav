#include <gtest/gtest.h>

#include <algorithm>
#include <cstdint>
#include <vector>

#include "dynnav_nav2_cpp/history_grid_search.hpp"

namespace
{

using dynnav_nav2_cpp::HistoryHazard;
using dynnav_nav2_cpp::HistorySearchConfig;
using dynnav_nav2_cpp::exactHistoryReturnProbability;
using dynnav_nav2_cpp::planHistoryGridPath;
using dynnav_nav2_cpp::robustPairwiseHistoryReturnProbability;

TEST(HistoryGridSearch, SameCellReliabilityDependsOnActivatedHistory)
{
  const std::size_t width = 5;
  const std::size_t height = 3;
  const std::vector<std::uint8_t> costs(width * height, 0U);
  const std::vector<std::size_t> safe{5U};  // (0,1)
  const std::vector<HistoryHazard> hazards{{6U, 7U, 5U, 0.8}};
  const HistorySearchConfig config{};

  EXPECT_DOUBLE_EQ(
    exactHistoryReturnProbability(width, height, costs, 7U, safe, hazards, 0U, config),
    1.0);
  EXPECT_NEAR(
    exactHistoryReturnProbability(width, height, costs, 7U, safe, hazards, 1U, config),
    0.2,
    1.0e-12);
}

TEST(HistoryGridSearch, PlannerAvoidsActionTriggeredReturnClosure)
{
  const std::size_t width = 5;
  const std::size_t height = 3;
  const std::vector<std::uint8_t> costs(width * height, 0U);
  const std::vector<std::size_t> safe{5U};
  const std::vector<HistoryHazard> hazards{{6U, 7U, 5U, 0.8}};
  HistorySearchConfig config;
  config.recoverability_weight = 4.0;

  const auto result = planHistoryGridPath(
    width, height, costs, 5U, 9U, safe, hazards, 0U, config);

  ASSERT_TRUE(result.success);
  EXPECT_EQ(result.path.front(), 5U);
  EXPECT_EQ(result.path.back(), 9U);
  EXPECT_EQ(result.final_active_mask, 0U);
  EXPECT_DOUBLE_EQ(result.final_return_probability, 1.0);
  EXPECT_TRUE(std::find(result.path.begin(), result.path.end(), 7U) == result.path.end() ||
    std::find(result.path.begin(), result.path.end(), 6U) == result.path.end());
}

TEST(HistoryGridSearch, OnlineReplanRetainsActivatedMask)
{
  const std::size_t width = 5;
  const std::size_t height = 3;
  const std::vector<std::uint8_t> costs(width * height, 0U);
  const std::vector<std::size_t> safe{5U};
  const std::vector<HistoryHazard> hazards{{6U, 7U, 5U, 0.8}};
  const HistorySearchConfig config{};

  const auto result = planHistoryGridPath(
    width, height, costs, 7U, 9U, safe, hazards, 1U, config);

  ASSERT_TRUE(result.success);
  EXPECT_EQ(result.final_active_mask, 1U);
  EXPECT_NEAR(result.final_return_probability, 0.2, 1.0e-12);
  EXPECT_NEAR(result.minimum_return_probability, 0.2, 1.0e-12);
}


TEST(HistoryGridSearch, RobustPairwiseParallelReturnUsesWorstCaseJointClosure)
{
  const std::size_t width = 3;
  const std::size_t height = 3;
  std::vector<std::uint8_t> costs(width * height, 0U);
  costs[4U] = 254U;
  const std::vector<std::size_t> safe{3U};
  const std::vector<HistoryHazard> hazards{
    {2U, 1U, 1U, 0.5},
    {8U, 7U, 7U, 0.5},
  };
  HistorySearchConfig independent;
  HistorySearchConfig robust;
  robust.robust_pairwise_dependence = true;
  robust.max_hazard_cells = 2U;

  EXPECT_NEAR(
    exactHistoryReturnProbability(width, height, costs, 5U, safe, hazards, 3U, independent),
    0.75,
    1.0e-12);
  EXPECT_NEAR(
    robustPairwiseHistoryReturnProbability(width, height, costs, 5U, safe, hazards, 3U, robust),
    0.5,
    1.0e-12);

  robust.pairwise_joint_lower = 0.0;
  robust.pairwise_joint_upper = 0.0;
  EXPECT_NEAR(
    robustPairwiseHistoryReturnProbability(width, height, costs, 5U, safe, hazards, 3U, robust),
    1.0,
    1.0e-12);
}

TEST(HistoryGridSearch, RobustPairwiseSerialReturnHasOppositeDependenceSensitivity)
{
  const std::size_t width = 4;
  const std::size_t height = 1;
  const std::vector<std::uint8_t> costs(width * height, 0U);
  const std::vector<std::size_t> safe{0U};
  const std::vector<HistoryHazard> hazards{
    {0U, 1U, 1U, 0.5},
    {2U, 3U, 2U, 0.5},
  };
  HistorySearchConfig robust;
  robust.robust_pairwise_dependence = true;
  robust.max_hazard_cells = 2U;

  EXPECT_NEAR(
    robustPairwiseHistoryReturnProbability(width, height, costs, 3U, safe, hazards, 3U, robust),
    0.0,
    1.0e-12);

  robust.pairwise_joint_lower = 0.5;
  robust.pairwise_joint_upper = 0.5;
  EXPECT_NEAR(
    robustPairwiseHistoryReturnProbability(width, height, costs, 3U, safe, hazards, 3U, robust),
    0.5,
    1.0e-12);
}

TEST(HistoryGridSearch, RobustPairwisePlannerChoosesTriggerFreeDetour)
{
  const std::size_t width = 5;
  const std::size_t height = 3;
  std::vector<std::uint8_t> costs(width * height, 254U);
  for (std::size_t x = 0; x < width; ++x) {
    costs[x] = 0U;
    costs[10U + x] = 0U;
  }
  costs[5U] = 0U;
  costs[9U] = 0U;

  const std::vector<std::size_t> safe{0U};
  const std::vector<HistoryHazard> hazards{
    {2U, 3U, 1U, 0.5},
    {3U, 4U, 11U, 0.5},
  };

  HistorySearchConfig independent;
  independent.recoverability_weight = 12.0;
  independent.max_hazard_cells = 2U;
  const auto independent_result = planHistoryGridPath(
    width, height, costs, 0U, 4U, safe, hazards, 0U, independent);

  HistorySearchConfig robust;
  robust.recoverability_weight = 12.0;
  robust.robust_pairwise_dependence = true;
  robust.max_hazard_cells = 2U;
  const auto robust_result = planHistoryGridPath(
    width, height, costs, 0U, 4U, safe, hazards, 0U, robust);

  ASSERT_TRUE(independent_result.success);
  ASSERT_TRUE(robust_result.success);
  EXPECT_EQ(independent_result.path.size() - 1U, 4U);
  EXPECT_EQ(independent_result.final_active_mask, 3U);
  EXPECT_NEAR(independent_result.final_return_probability, 0.75, 1.0e-12);

  EXPECT_EQ(robust_result.path.size() - 1U, 8U);
  EXPECT_EQ(robust_result.final_active_mask, 0U);
  EXPECT_DOUBLE_EQ(robust_result.final_return_probability, 1.0);
}


TEST(HistoryGridSearch, MultiCellClosureFootprintCanSealWideCorridor)
{
  const std::size_t width = 5;
  const std::size_t height = 5;
  const std::vector<std::uint8_t> costs(width * height, 0U);
  const std::vector<std::size_t> safe{10U, 15U, 20U};
  HistoryHazard hazard{7U, 8U, 6U, 1.0};
  hazard.closure_indices = {6U, 11U, 16U, 21U};
  const std::vector<HistoryHazard> hazards{hazard};
  const HistorySearchConfig config{};

  EXPECT_DOUBLE_EQ(
    exactHistoryReturnProbability(width, height, costs, 14U, safe, hazards, 0U, config),
    1.0);
  EXPECT_DOUBLE_EQ(
    exactHistoryReturnProbability(width, height, costs, 14U, safe, hazards, 1U, config),
    0.0);
}

}  // namespace
