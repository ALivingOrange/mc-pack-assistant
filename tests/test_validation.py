"""Tests for the item-ID / shaped-recipe validation helpers."""

from __future__ import annotations

import pytest

# Importing the customizer package triggers __init__.py, which loads the
# agent module (google-adk / google-genai). Skip if unavailable.
pytest.importorskip(
    "modules.customizer.grounded_recipe_modifier_agent",
    reason="customizer package requires google-adk / google-genai to be installed",
)

from modules.customizer import data, validation  # noqa: E402

# ---------- validate_item_id ----------


def test_validate_item_id_accepts_tag() -> None:
    assert validation.validate_item_id("#minecraft:logs") is True


def test_validate_item_id_accepts_known_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(data, "VALID_ITEM_IDS", {"minecraft:dirt"})
    assert validation.validate_item_id("minecraft:dirt") is True


def test_validate_item_id_rejects_unknown_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(data, "VALID_ITEM_IDS", {"minecraft:dirt"})
    assert validation.validate_item_id("minecraft:nonexistent") is False


def test_validate_item_id_accepts_pipe_options_when_all_valid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(data, "VALID_ITEM_IDS", {"minecraft:oak_planks", "minecraft:birch_planks"})
    assert validation.validate_item_id("minecraft:oak_planks|minecraft:birch_planks") is True


def test_validate_item_id_rejects_pipe_options_when_any_invalid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(data, "VALID_ITEM_IDS", {"minecraft:oak_planks"})
    assert validation.validate_item_id("minecraft:oak_planks|minecraft:fake") is False


# ---------- validate_shaped_recipe ----------


def test_validate_shaped_recipe_accepts_valid_3x3() -> None:
    result = validation.validate_shaped_recipe(
        shape=["AAA", "A A", "AAA"],
        ingredients={"minecraft:oak_planks": "A"},
    )
    assert result == {"valid": True}


def test_validate_shaped_recipe_rejects_too_tall() -> None:
    result = validation.validate_shaped_recipe(
        shape=["A", "A", "A", "A"],
        ingredients={"minecraft:stick": "A"},
    )
    assert result["valid"] is False
    assert "1-3 rows" in result["error_message"]


def test_validate_shaped_recipe_rejects_missing_ingredient() -> None:
    result = validation.validate_shaped_recipe(
        shape=["AB", "BA"],
        ingredients={"minecraft:dirt": "A"},
    )
    assert result["valid"] is False
    assert "B" in result["error_message"]


def test_validate_shaped_recipe_rejects_duplicate_letters() -> None:
    result = validation.validate_shaped_recipe(
        shape=["AA", "AA"],
        ingredients={"minecraft:dirt": "A", "minecraft:stone": "A"},
    )
    assert result["valid"] is False
    assert "Duplicate" in result["error_message"]


def test_validate_shaped_recipe_rejects_unused_ingredient() -> None:
    result = validation.validate_shaped_recipe(
        shape=["A", "A"],
        ingredients={"minecraft:dirt": "A", "minecraft:stone": "B"},
    )
    assert result["valid"] is False
    assert "B" in result["error_message"]
