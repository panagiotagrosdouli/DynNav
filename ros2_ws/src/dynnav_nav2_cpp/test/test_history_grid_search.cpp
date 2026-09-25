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


TEST(HistoryGridSearch, NoActiveHazardsStillChecksStaticSafeReachability)
{
  const std::size_t width = 3;
  const std::size_t height = 1;
  const std::vector<std::uint8_t> costs{0U, 254U, 0U};
  const std::vector<std::size_t> safe{0U};
  const std::vector<HistoryHazard> hazards;
  const HistorySearchConfig config{};

  EXPECT_DOUBLE_EQ(
    exactHistoryReturnProbability(width, height, costs, 2U, safe, hazards, 0U, config),
    0.0);
}

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


TEST(HistoryGridSearch, SharedClosureCellIsOneLatentEvent)
{
  // Two different executed triggers activate the same physical bridge closure.
  // Activating both must not square the event probability.
  const std::size_t width = 5;
  const std::size_t height = 3;
  std::vector<std::uint8_t> costs(width * height, 254U);
  for (const auto index : std::vector<std::size_t>{5U, 6U, 7U, 8U, 9U, 2U, 3U}) {
    costs[index] = 0U;
  }
  const std::vector<std::size_t> safe{5U};
  const std::vector<HistoryHazard> hazards{
    {7U, 2U, 6U, 0.5},
    {2U, 3U, 6U, 0.5},
  };
  const HistorySearchConfig config{};

  EXPECT_NEAR(
    exactHistoryReturnProbability(width, height, costs, 9U, safe, hazards, 0b11U, config),
    0.5,
    1.0e-12);
}

TEST(HistoryGridSearch, SharedClosureCellRejectsConflictingProbabilities)
{
  const std::size_t width = 5;
  const std::size_t height = 3;
  const std::vector<std::uint8_t> costs(width * height, 0U);
  const std::vector<std::size_t> safe{5U};
  const std::vector<HistoryHazard> hazards{
    {6U, 7U, 5U, 0.4},
    {7U, 8U, 5U, 0.7},
  };
  const HistorySearchConfig config{};

  EXPECT_THROW(
    exactHistoryReturnProbability(width, height, costs, 9U, safe, hazards, 0b11U, config),
    std::invalid_argument);
}

}  // namespace
