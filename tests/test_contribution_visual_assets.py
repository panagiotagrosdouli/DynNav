from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VISUAL_DIR = ROOT / "assets" / "contributions"


def test_every_contribution_has_an_accessible_overview_svg() -> None:
    expected = [VISUAL_DIR / f"C{i:02d}_overview.svg" for i in range(1, 27)]
    assert all(path.is_file() for path in expected)

    for index, path in enumerate(expected, start=1):
        root = ET.parse(path).getroot()
        assert root.tag.endswith("svg")
        title = root.find("{http://www.w3.org/2000/svg}title")
        desc = root.find("{http://www.w3.org/2000/svg}desc")
        if title is not None:
            assert f"C{index:02d}" in (title.text or "")
        if desc is not None:
            assert (desc.text or "").strip()
        assert path.stat().st_size > 500


def test_visual_gallery_references_all_contributions() -> None:
    gallery = (ROOT / "docs" / "CONTRIBUTION_VISUAL_GALLERY.md").read_text(encoding="utf-8")
    for index in range(1, 27):
        assert f"C{index:02d}_overview.svg" in gallery
