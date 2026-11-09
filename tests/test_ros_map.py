import numpy as np
import yaml
from PIL import Image

from dynnav.mapping.ros_map import load_ros_map


def _write_ros_map(directory, pixels: np.ndarray, *, origin: list[float] | None = None) -> str:
    image_path = directory / "map.pgm"
    Image.fromarray(pixels.astype(np.uint8), mode="L").save(image_path)
    yaml_path = directory / "map.yaml"
    yaml_path.write_text(
        yaml.safe_dump(
            {
                "image": image_path.name,
                "resolution": 0.5,
                "origin": origin or [1.0, 2.0, 0.0],
                "negate": 0,
                "occupied_thresh": 0.65,
                "free_thresh": 0.2,
                "mode": "trinary",
            }
        ),
        encoding="utf-8",
    )
    return str(yaml_path)


def test_load_ros_map_flips_image_y_and_blocks_unknown_by_default(tmp_path) -> None:
    # Image rows are top-to-bottom; map cells are indexed bottom-to-top.
    pixels = np.array([[255, 0], [0, 128]], dtype=np.uint8)
    ros_map = load_ros_map(_write_ros_map(tmp_path, pixels))

    assert (ros_map.grid.width, ros_map.grid.height) == (2, 2)
    assert (0, 1) not in ros_map.grid.obstacles
    assert {(1, 1), (0, 0), (1, 0)} <= ros_map.grid.obstacles


def test_unknown_policy_and_world_cell_transform(tmp_path) -> None:
    pixels = np.array([[255, 0], [0, 128]], dtype=np.uint8)
    ros_map = load_ros_map(_write_ros_map(tmp_path, pixels), unknown_as_obstacle=False)

    assert (1, 0) not in ros_map.grid.obstacles
    assert ros_map.world_to_cell(1.25, 2.25) == (0, 0)
    assert ros_map.cell_center((1, 1)) == (1.75, 2.75)


def test_world_to_cell_respects_origin_yaw(tmp_path) -> None:
    pixels = np.full((2, 2), 255, dtype=np.uint8)
    ros_map = load_ros_map(
        _write_ros_map(tmp_path, pixels, origin=[3.0, -1.0, np.pi / 2]),
    )

    assert ros_map.world_to_cell(2.75, -0.75) == (0, 0)
    assert np.allclose(ros_map.cell_center((1, 0)), (2.75, -0.25))
