#include "dynnav_nav2_cpp/history_observation.hpp"
#include "gtest/gtest.h"

TEST(HistoryObservation, RejectsMalformedCellsWithoutNarrowing)
{
  for (const auto * value : {"-1:0", "+1:0", "1junk:0", "1:0junk", "1::0", ":1:0", "1:0:",
      "4294967296:0", "18446744073709551616:0", " 1:0"})
  {
    EXPECT_THROW(dynnav_nav2_cpp::parseCell(value), std::exception) << value;
  }
  EXPECT_EQ(dynnav_nav2_cpp::parseCell("12:34"), dynnav_nav2_cpp::HistoryCell(12U, 34U));
}

TEST(HistoryObservation, RequiresExactAdjacentDirectedTransition)
{
  for (const auto * value : {">1:0>2:0", "1:0>>2:0", "1:0>2:0>", "1:0", "1:0>2:0junk"}) {
    EXPECT_THROW(dynnav_nav2_cpp::parseTransition(value), std::exception) << value;
  }
  EXPECT_TRUE(dynnav_nav2_cpp::adjacentTransition(dynnav_nav2_cpp::parseTransition("1:0>2:0")));
  EXPECT_FALSE(dynnav_nav2_cpp::adjacentTransition(dynnav_nav2_cpp::parseTransition("1:0>1:0")));
  EXPECT_FALSE(dynnav_nav2_cpp::adjacentTransition(dynnav_nav2_cpp::parseTransition("1:0>2:1")));
}

TEST(HistoryObservation, ChecksMeasurementFrameAgeAndOrdering)
{
  const auto valid = dynnav_nav2_cpp::parseObservation("v1|map|2000000000|1:0>2:0", "map", 2100000000ULL);
  EXPECT_EQ(valid.stamp_ns, 2000000000ULL);
  for (const auto * value : {"1:0>2:0", "v1|odom|2000000000|1:0>2:0", "v1|map|0|1:0>2:0",
      "v1|map|100000000|1:0>2:0", "v1|map|3000000000|1:0>2:0", "v1|map|2000000000|1:0>1:0"})
  {
    EXPECT_THROW(dynnav_nav2_cpp::parseObservation(value, "map", 2100000000ULL), std::exception) << value;
  }
  EXPECT_THROW(
    dynnav_nav2_cpp::parseObservation("v1|map|2000000000|1:0>2:0", "map", 2100000000ULL, 2000000000ULL),
    std::invalid_argument);
}
