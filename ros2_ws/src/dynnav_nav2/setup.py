from setuptools import setup

package_name = "dynnav_nav2"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", ["launch/dynnav_planner_bridge.launch.py"]),
        ("share/" + package_name + "/config", ["config/dynnav_planner_bridge.yaml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="DynNav maintainers",
    maintainer_email="maintainer@example.com",
    description="ROS 2 integration scaffold for DynNav planners.",
    license="MIT",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "dynnav_planner_bridge = dynnav_nav2.dynnav_planner_bridge:main",
        ],
    },
)
