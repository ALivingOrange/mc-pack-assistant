"""Tests for the item-ID / shaped-recipe validation helpers.

Both functions currently live in the monolithic
`modules.customizer.grounded_recipe_modifier_agent` module. Phase 3.3 of the
cleanup plan extracts them to a `validation.py` module — at that point the
imports in this file should be updated.

Importing the agent module is gated on google-adk / google-genai being
installed; if they aren't, the tests skip cleanly.
"""

from __future__ import annotations

import pytest

agent = pytest.importorskip(
    "modules.customizer.grounded_recipe_modifier_agent",
    reason="agent module requires google-adk / google-genai to be installed",
)


# ---------- validate_item_id ----------


def test_validate_item_id_accepts_tag() -> None:
    assert agent.validate_item_id("#minecraft:logs") is True


def test_validate_item_id_accepts_known_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(agent, "VALID_ITEM_IDS", {"minecraft:dirt"})
    assert agent.validate_item_id("minecraft:dirt") is True


def test_validate_item_id_rejects_unknown_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(agent, "VALID_ITEM_IDS", {"minecraft:dirt"})
    assert agent.validate_item_id("minecraft:nonexistent") is False


def test_validate_item_id_accepts_pipe_options_when_all_valid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(agent, "VALID_ITEM_IDS", {"minecraft:oak_planks", "minecraft:birch_planks"})
    assert agent.validate_item_id("minecraft:oak_planks|minecraft:birch_planks") is True


def test_validate_item_id_rejects_pipe_options_when_any_invalid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(agent, "VALID_ITEM_IDS", {"minecraft:oak_planks"})
    assert agent.validate_item_id("minecraft:oak_planks|minecraft:fake") is False


# ---------- validate_shaped_recipe ----------


def test_validate_shaped_recipe_accepts_valid_3x3() -> None:
    result = agent.validate_shaped_recipe(
        shape=["AAA", "A A", "AAA"],
        ingredients={"minecraft:oak_planks": "A"},
    )
    assert result == {"valid": True}


def test_validate_shaped_recipe_rejects_too_tall() -> None:
    result = agent.validate_shaped_recipe(
        shape=["A", "A", "A", "A"],
        ingredients={"minecraft:stick": "A"},
    )
    assert result["valid"] is False
    assert "1-3 rows" in result["error_message"]


def test_validate_shaped_recipe_rejects_missing_ingredient() -> None:
    result = agent.validate_shaped_recipe(
        shape=["AB", "BA"],
        ingredients={"minecraft:dirt": "A"},  # B is used in shape but not defined
    )
    assert result["valid"] is False
    assert "B" in result["error_message"]


def test_validate_shaped_recipe_rejects_duplicate_letters() -> None:
    result = agent.validate_shaped_recipe(
        shape=["AA", "AA"],
        ingredients={"minecraft:dirt": "A", "minecraft:stone": "A"},
    )
    assert result["valid"] is False
    assert "Duplicate" in result["error_message"]


def test_validate_shaped_recipe_rejects_unused_ingredient() -> None:
    result = agent.validate_shaped_recipe(
        shape=["A", "A"],
        ingredients={"minecraft:dirt": "A", "minecraft:stone": "B"},  # B never appears in shape
    )
    assert result["valid"] is False
    assert "B" in result["error_message"]
