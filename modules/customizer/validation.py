from . import data


def validate_item_id(item_id: str) -> bool:
    """Check if an item ID is valid. Tags (prefixed with #) are assumed correct."""
    if item_id.startswith("#"):
        return True

    if "|" in item_id:
        return all(validate_item_id(id.strip()) for id in item_id.split("|"))

    return item_id in data.VALID_ITEM_IDS


def validate_shaped_recipe(shape: list[str], ingredients: dict) -> dict:
    """Validates the shape and ingredients for a shaped recipe.

    Args:
        shape: A list of strings representing the crafting grid pattern.
        ingredients: A dict mapping item identifiers to letters (A-I).

    Returns:
        A dict with 'valid' (bool) and 'error_message' (str) if invalid.
    """
    if not isinstance(shape, list):
        return {"valid": False, "error_message": "Shape must be a list of strings"}

    if len(shape) < 1 or len(shape) > 3:
        return {"valid": False, "error_message": "Shape must have 1-3 rows"}

    for i, row in enumerate(shape):
        if not isinstance(row, str):
            return {"valid": False, "error_message": f"Row {i} must be a string"}

        if len(row) < 1 or len(row) > 3:
            return {"valid": False, "error_message": f"Row {i} must be 1-3 characters long"}

        for char in row:
            if char not in "ABCDEFGHI ":
                return {
                    "valid": False,
                    "error_message": (
                        f"Row {i} contains invalid character '{char}'. "
                        "Only A-I and spaces are allowed"
                    ),
                }

    letters_in_shape = set()
    for row in shape:
        for char in row:
            if char != " ":
                letters_in_shape.add(char)

    if not isinstance(ingredients, dict):
        return {"valid": False, "error_message": "Ingredients must be a dictionary"}

    letters_in_ingredients = set(ingredients.values())

    for letter in letters_in_ingredients:
        if not isinstance(letter, str) or len(letter) != 1 or letter not in "ABCDEFGHI":
            return {
                "valid": False,
                "error_message": f"Invalid ingredient letter '{letter}'. Must be A-I",
            }

    if len(letters_in_ingredients) != len(ingredients):
        return {
            "valid": False,
            "error_message": (
                "Duplicate letters found in ingredients. "
                "Each ingredient must map to a unique letter"
            ),
        }

    missing_ingredients = letters_in_shape - letters_in_ingredients
    if missing_ingredients:
        return {
            "valid": False,
            "error_message": (
                f"Letters {missing_ingredients} used in shape but not defined in ingredients"
            ),
        }

    unused_ingredients = letters_in_ingredients - letters_in_shape
    if unused_ingredients:
        return {
            "valid": False,
            "error_message": (
                f"Letters {unused_ingredients} defined in ingredients but not used in shape"
            ),
        }

    return {"valid": True}
