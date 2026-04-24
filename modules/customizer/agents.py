import logging
import os
from pathlib import Path

from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.models.google_llm import Gemini

from .config import MODEL_NAME, OUTPUT_PATH, retry_config
from .tools import (
    add_cooking_recipe,
    add_shaped_recipe,
    add_shapeless_recipe,
    add_smithing_recipe,
    add_stonecutting_recipe,
    find_recipes,
    remove_recipes,
    replace_recipe_items,
    search_item_ids,
)

logger = logging.getLogger(__name__)


# Load API key: prefer existing env var, else fall back to cache file if present.
if not os.environ.get("GOOGLE_API_KEY"):
    _api_key_path = Path(__file__).parent.parent.parent / "cache" / ".api_key"
    try:
        with open(_api_key_path) as _file:
            os.environ["GOOGLE_API_KEY"] = _file.read().strip()
    except OSError:
        logger.warning(
            "GOOGLE_API_KEY not set and %s not readable; agent calls will fail until one is "
            "provided.",
            _api_key_path,
        )

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
if not OUTPUT_PATH.exists():
    with open(OUTPUT_PATH, "x") as _file:
        _file.write("ServerEvents.recipes(event =>{\n\n\n})")
else:
    logger.info("Repeat test. Make sure the output ends in a line with })!")


searcher_agent = LlmAgent(
    name="searcher_agent",
    model=Gemini(model=MODEL_NAME, retry_options=retry_config),
    instruction="""You are a smart assistant to aid in the custom integration of Minecraft mods.
    Your job is to use your tools to compile relevant information on the game's data. Your are part of a pipeline which makes changes to recipe data.

    When given a user's query. you should make an item ID search to find information on item IDs. Use as many search queries as you feel necessary.
    Then, use those item IDs in your find_recipes tool.
    Bear in mind that searching for item ideas uses fuzzier semantic matching, while find_recipes requires exact item IDs to work.

    Once you've found relevant information, summarize along with the user's input and output it to be passed onto the agent which can add, modify, or remove recipes.
    Do not include suggestions in your summary; keep it only to accurate data.
    Make sure that the agent gets real, correct item IDs and recipe data!

    **Your output is sent to another agent. Don't reply as if speaking directly to the user; only your fellow agent will see it.**

    If any tool returns status "error", check the error message and see if you can address it.
    """,
    tools=[search_item_ids, find_recipes],
    output_key="search_result_summary",
)


recipe_modifier_agent = LlmAgent(
    name="recipe_modifier_agent",
    model=Gemini(model=MODEL_NAME, retry_options=retry_config),
    instruction="""You are a smart assistant to aid in the custom integration of Minecraft mods by adding custom recipes or changing or removing existing recipes.
    Your only job is manipulating recipes. So, if there's a more vague query, like "Make copper harder to get," don't worry about non-recipe interventions such as loot table changes. *Don't even mention them.*
    Try to bear in mind the intended purpose of blocks as you can. For instance, if you decrease the yield of copper blocks to make copper harder to get from structures, make sure it also decreases how many ingots it takes to craft them so they still fulfill the purpose of compressing ingot storage.
    The mod loader being used is Fabric.
    After processing the information from the searcher, take a deep breath and write a paragraph considering how to fulfill the request through the tools that you have available.
    All recipe-modification tools should receive a comment explaining what you're using them to add as their first argument.

    # This is your current job and the most relevant game data:
    {search_result_summary}

    If any tool returns status "error", check the error message and see if you can address it.
    """,
    tools=[
        add_shapeless_recipe,
        add_shaped_recipe,
        add_smithing_recipe,
        add_cooking_recipe,
        add_stonecutting_recipe,
        remove_recipes,
        replace_recipe_items,
    ],
)

root_agent = SequentialAgent(
    name="RecipeModifierPipeline", sub_agents=[searcher_agent, recipe_modifier_agent]
)
