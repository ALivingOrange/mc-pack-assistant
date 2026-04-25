"""Tests for the mod-jar item-ID extraction helper."""

from __future__ import annotations

import zipfile
from pathlib import Path

from modules.pipeline.item_id_extractor import extract_ids_from_jar


def test_extract_ids_from_jar_picks_up_item_and_block_models(tmp_path: Path) -> None:
    jar_path = tmp_path / "testmod.jar"
    with zipfile.ZipFile(jar_path, "w") as jar:
        jar.writestr("assets/testmod/models/item/foo.json", "{}")
        jar.writestr("assets/testmod/models/block/bar.json", "{}")
        jar.writestr("assets/testmod/textures/item/foo.png", b"")

    items, blocks = extract_ids_from_jar(jar_path)

    assert items == {"testmod:foo"}
    assert blocks == {"testmod:bar"}


def test_extract_ids_from_jar_empty_jar_returns_empty_sets(tmp_path: Path) -> None:
    jar_path = tmp_path / "empty.jar"
    with zipfile.ZipFile(jar_path, "w"):
        pass

    items, blocks = extract_ids_from_jar(jar_path)

    assert items == set()
    assert blocks == set()
