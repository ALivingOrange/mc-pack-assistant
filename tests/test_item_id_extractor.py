"""Tests for the mod-jar item-ID extraction helper."""

from __future__ import annotations

import importlib.util
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXTRACTOR_PATH = ROOT / "helper-scripts" / "ui" / "item_id_extractor.py"


def _load_extractor():
    """Load item_id_extractor.py by path (its directory contains a hyphen,
    so it isn't importable as a normal package)."""
    spec = importlib.util.spec_from_file_location("item_id_extractor", EXTRACTOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["item_id_extractor"] = module
    spec.loader.exec_module(module)
    return module


def test_extract_ids_from_jar_picks_up_item_and_block_models(tmp_path: Path) -> None:
    jar_path = tmp_path / "testmod.jar"
    with zipfile.ZipFile(jar_path, "w") as jar:
        # Item model → testmod:foo
        jar.writestr("assets/testmod/models/item/foo.json", "{}")
        # Block model → testmod:bar
        jar.writestr("assets/testmod/models/block/bar.json", "{}")
        # Unrelated file → ignored
        jar.writestr("assets/testmod/textures/item/foo.png", b"")

    extractor = _load_extractor()
    items, blocks = extractor.extract_ids_from_jar(jar_path)

    assert items == {"testmod:foo"}
    assert blocks == {"testmod:bar"}


def test_extract_ids_from_jar_empty_jar_returns_empty_sets(tmp_path: Path) -> None:
    jar_path = tmp_path / "empty.jar"
    with zipfile.ZipFile(jar_path, "w"):
        pass

    extractor = _load_extractor()
    items, blocks = extractor.extract_ids_from_jar(jar_path)

    assert items == set()
    assert blocks == set()
