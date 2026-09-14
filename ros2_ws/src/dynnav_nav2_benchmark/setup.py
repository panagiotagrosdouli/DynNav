from glob import glob

from setuptools import find_packages, setup

package_name = "dynnav_nav2_benchmark"

setup(
    name=package_name,
    version="0.2.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (f"share/{package_name}/config", glob("config/*.yaml")),
        (f"share/{package_name}/launch", glob("launch/*.launch.py")),
        (f"share/{package_name}/models", glob("models/*.sdf")),
    ],
    install_requires=["setuptools", "PyYAML"],
    zip_safe=True,
    maintainer="Panagiota Grosdouli",
    maintainer_email="75089541+panagiotagrosdouli@users.noreply.github.com",
    description="Paired static and dynamic Nav2 benchmarks for DynNav.",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "static_planner_benchmark = dynnav_nav2_benchmark.benchmark_runner:main",
            "dynamic_execution_benchmark = dynnav_nav2_benchmark.dynamic_runner:main",
            "history_dynamic_execution_benchmark = dynnav_nav2_benchmark.history_dynamic_runner:main",
        ],
    },
)
