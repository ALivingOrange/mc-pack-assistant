from ..data import ALL_RECIPES
from ..rag import ITEM_SEARCHER


def search_item_ids(queries: list[str], top_k_per_query: int = 8) -> dict:
    """
    Search for item IDs in the pack relevant to the given queries using semantic search.

    Args:
        queries: List of query strings to search for.
                 Examples:
                 - ["diamond tools"]
                 - ["diamond tools", "iron armor", "redstone components"]

        top_k_per_query: Number of results to return per query (default 8, max 15)

    Returns:
        A dict with:
        - 'queries': The list of queries searched
        - 'results': Dict mapping each query to its list of results
        - 'total_unique_items': Number of unique items found across all queries

    Example usage:
        search_item_ids(["diamond sword"])
        -> Returns top 8 items matching "diamond sword"

        search_item_ids(["red blocks", "blue blocks"], top_k_per_query=5)
        -> Returns top 5 items for each query
    """
    top_k_per_query = max(1, min(top_k_per_query, 15))

    try:
        all_results = {}
        all_items = set()

        for query in queries:
            results = ITEM_SEARCHER.search(query, top_k=top_k_per_query)

            formatted_results = [
                {"item_id": item_id, "relevance_score": round(score, 3)}
                for item_id, score in results
            ]

            all_results[query] = formatted_results
            all_items.update(item_id for item_id, _ in results)

        return {
            "status": "success",
            "queries": queries,
            "results": all_results,
            "total_unique_items": len(all_items),
        }

    except Exception as e:
        return {"status": "error", "error_message": f"Search failed: {str(e)}"}


def find_recipes(query_item: str, search_by: str):
    """
    Searches all of the recipes in the modpack, using query_item.
    Recipes with query_item in either the result or in ingredients depending on mode.
    Unlike search_item_ids, this is an *exact match*.
    Args:
        query_item: The item string to look for (e.g., 'minecraft:dandelion').
        search_by: Either 'result' or 'ingredient'.
    """
    matches = []
    recipes = ALL_RECIPES

    if recipes == []:
        return {"status": "error", "error_message": "List of recipes is empty!"}

    for recipe in recipes:
        data = recipe.get("data", {})

        if search_by == "result":
            res = data.get("result", {})
            if isinstance(res, dict):
                if res.get("item") == query_item:
                    matches.append(recipe)
            elif isinstance(res, str):
                if res == query_item:
                    matches.append(recipe)

        elif search_by == "ingredient":
            found = False

            if "ingredients" in data:
                for ing in data["ingredients"]:
                    if isinstance(ing, dict) and ing.get("item") == query_item:
                        found = True
                    elif isinstance(ing, list):
                        for sub_ing in ing:
                            if sub_ing.get("item") == query_item:
                                found = True

            elif "key" in data:
                for _char, ing_data in data["key"].items():
                    if isinstance(ing_data, dict) and ing_data.get("item") == query_item:
                        found = True
                    elif isinstance(ing_data, list):
                        for sub_ing in ing_data:
                            if sub_ing.get("item") == query_item:
                                found = True

            elif "ingredient" in data:
                ing = data["ingredient"]
                if isinstance(ing, dict) and ing.get("item") == query_item:
                    found = True

            if found:
                matches.append(recipe)

    return {"status": "success", "matches": matches}
