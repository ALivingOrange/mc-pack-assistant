import logging

from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.models.google_llm import Gemini

from .config import MODEL_NAME, OUTPUT_PATH, load_api_key, retry_config
from .integrations import INTEGRATIONS
from .tools import find_recipes, search_item_ids

logger = logging.getLogger(__name__)


load_api_key()

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


root_agent = SequentialAgent(
    name="ModpackCustomizerPipeline",
    sub_agents=[searcher_agent, *(i.build_agent() for i in INTEGRATIONS)],
)
