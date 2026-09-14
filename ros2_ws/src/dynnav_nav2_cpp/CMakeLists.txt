cmake_minimum_required(VERSION 3.8)
project(dynnav_nav2_cpp)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(nav2_core REQUIRED)
find_package(nav2_costmap_2d REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(nav2_util REQUIRED)
find_package(pluginlib REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)

add_library(dynnav_grid_search STATIC
  src/grid_search.cpp
  src/history_grid_search.cpp
)
set_target_properties(dynnav_grid_search PROPERTIES POSITION_INDEPENDENT_CODE ON)
target_include_directories(dynnav_grid_search PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)

add_library(dynnav_global_planner SHARED
  src/dynnav_global_planner.cpp
)
target_include_directories(dynnav_global_planner PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)
target_link_libraries(dynnav_global_planner dynnav_grid_search)

ament_target_dependencies(dynnav_global_planner
  rclcpp
  nav2_core
  nav2_costmap_2d
  nav_msgs
  geometry_msgs
  nav2_util
  pluginlib
  tf2_ros
  tf2_geometry_msgs
)

pluginlib_export_plugin_description_file(nav2_core dynnav_global_planner_plugin.xml)

install(TARGETS dynnav_grid_search dynnav_global_planner
  EXPORT export_${PROJECT_NAME}
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

install(DIRECTORY include/
  DESTINATION include
)

install(DIRECTORY config/
  DESTINATION share/${PROJECT_NAME}/config
)

install(FILES dynnav_global_planner_plugin.xml
  DESTINATION share/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_cmake_gtest REQUIRED)

  ament_add_gtest(test_grid_search test/test_grid_search.cpp)
  target_link_libraries(test_grid_search dynnav_grid_search)
  target_include_directories(test_grid_search PRIVATE include)

  ament_add_gtest(test_history_grid_search test/test_history_grid_search.cpp)
  target_link_libraries(test_history_grid_search dynnav_grid_search)
  target_include_directories(test_history_grid_search PRIVATE include)

  ament_add_gtest(test_plugin_load test/test_plugin_load.cpp)
  ament_target_dependencies(test_plugin_load nav2_core pluginlib)
  add_dependencies(test_plugin_load dynnav_global_planner)
endif()

ament_export_include_directories(include)
ament_export_targets(export_${PROJECT_NAME} HAS_LIBRARY_TARGET)
ament_export_dependencies(
  rclcpp
  nav2_core
  nav2_costmap_2d
  nav_msgs
  geometry_msgs
  nav2_util
  pluginlib
  tf2_ros
  tf2_geometry_msgs
)

ament_package()
