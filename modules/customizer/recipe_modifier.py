from google.genai import types

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search, AgentTool, ToolContext
from google.adk.code_executors import BuiltInCodeExecutor

import asyncio

import os
from pathlib import Path

# Load API key from file
api_key_path = Path(__file__).parent.parent.parent / ".api_key"
with open(api_key_path, 'r') as file:
    os.environ["GOOGLE_API_KEY"] = file.read().strip()

retry_config = types.HttpRetryOptions(
    attempts=5,  # Maximum retry attempts
    exp_base=7,  # Delay multiplier
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],  # Retry on these HTTP errors
)

# ====== TOOL DEFINITIONS =====================================================

def add_shapeless_recipe(comment: str, ingredients: dict, result: str,count: int, output_path: str) -> dict:
    """Writes to a KubeJS script to create a shapeless recipe with the given items.

    Args:
        comment: A string describing the recipe in natural language. Will be added
        to the script as a comment. Try to describe what mod each item is from.
        Ex: "Mix one each of blaze powder coal/charcoal, and gunpowder (all from vanilla) to make one fire charge from vanilla."

        ingredients: A dict containing the items in the recipe. Keys should be item
        identifiers, while values should be the number to be used (as integers).
        For cases with multiple ingredient options, separate each with '|' characters.
        Note that the count must be less than or equal to nine, as that's the maximum
        amount that the grid can fit.
        Ex: {"minecraft:blaze_powder"=1, "minecraft:coal|minecraft:charcoal"=1, "minecraft:gunpowder"=1}

        result: Item identifier of result as a string
        Ex: "minecraft:fire_charge"

        count: Amount of result produced. Ex: 1

        output_path: The file path for the script to be written in.
    """
 # Read output file
    try:
        with open(output_path, 'r') as file:
            lines:list[str] = file.readlines()
    except IOError as e:
        return {"status": "error", "error_message": ("Error reading file: " + str(e))}
# Remove last line (should be closing "})")        
    if lines: lines = lines[:-1]

# TO-DO: Validate Item IDs

# Add script to lines
    lines.append(f"\n\n# {comment}\n")
    lines.append("event.shapeless(\n")
    lines.append(f"\tItem.of('{result}', {count}),\n")
    lines.append("\t[\n")
    for key in ingredients:
        # Only specify count if >1
        if ingredients[key] == 1:
            lines.append(f"\t\t'{key}',\n")
        else:
            lines.append(f"\t\t'{ingredients[key]}x {key}',\n")
    # Remove comment from last ingredient
    lines[-1] = lines[-1][:-2] + "\n"
    
    lines.append("\t]\n")
    lines.append(")\n")
    lines.append("})")

# Write back to output file
    try:
        with open(output_path, 'w') as file:
            file.writelines(lines)
    except IOError as e:
        return {"status": "error", "error_message": ("Error writing file: " + str(e))}

    return {"status": "success"}

# ====== RECIPE MODIFIER AGENT ================================================
recipe_modifier_agent = LlmAgent(
    name="recipe_modifier_agent",
    model=Gemini(model="gemini-2.5-flash", retry_options=retry_config),
    instruction="""You are a smart assistant to aid in the custom integration of Minecraft mods by adding custom recipes or changing or removing existing recipes.

    Your only job is manipulating recipes.
    When given a request, take a deep breath and write a paragraph considering how to fulfill the request through the tools that you have available.
    All recipe-modification tools should receive a comment explaining what you're using them to add as their first argument.
    The output path should just be "test.txt" for now.
    For the moment, your only available tool is `add_shapeless_recipe()`. You will get more soon.

    If any tool returns status "error", check the error message and see if you can address it.
    """,
    tools=[add_shapeless_recipe],
    )


# ====== TEST SCRIPT ==========================================================

async def main():
    """Run an interactive terminal dialogue with the recipe modifier agent."""
    # Set up valid text file.
    if not os.path.exists("test.txt"):
        with open("test.txt", 'x') as file:
            file.write("ServerEvents.recipes(event =>{\n\n\n})")
    else:
        print("Repeat test. Make sure test.txt ends in a line with })!")
    
    print("=" * 70)
    print("MINECRAFT RECIPE MODIFIER AGENT - Interactive Test")
    print("=" * 70)
    print("\nThis agent can help you create custom Minecraft recipes.")
    print("Type 'quit' or 'exit' to end the conversation.\n")
    
    USER_ID = "default"
    
    # Initialize session and runner
    session_service = InMemorySessionService()
    runner = Runner(agent=recipe_modifier_agent, app_name="default", session_service=session_service)
    
    # Attempt to create new session or retrieve existing
    try:
        session = await session_service.create_session(app_name="default", user_id=USER_ID, session_id="default")
    except:
        session = await session_service.get_session(app_name="default", user_id=USER_ID, session_id="default")
    
    session_id = session.id
    print(f"Session started (ID: {session_id})")
    print("-" * 70)
    
    while True:
        try:
            # Get user input
            user_input = input("\nYou: ").strip()
            
            # Check for exit commands
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\nEnding session. Goodbye!")
                break
            
            # Skip empty inputs
            if not user_input:
                continue
            
            print("\nAgent: ", end="", flush=True)
            
            # Convert the query string to the ADK Content format
            query = types.Content(role="user", parts=[types.Part(text=user_input)])
            
            # Run the agent with streaming
            async for event in runner.run_async(user_id=USER_ID, session_id=session_id, new_message=query):
                # Check if the event contains valid content
                if event.content and event.content.parts:
                    # Filter out empty or "None" responses before printing
                    if event.content.parts[0].text != "None" and event.content.parts[0].text:
                        print(event.content.parts[0].text, end="", flush=True)
            
            print()  # Newline after response
            
        except KeyboardInterrupt:
            print("\n\nInterrupted by user. Ending session.")
            break
        except Exception as e:
            print(f"\nError: {e}")
            print("Continuing session...\n")
    
    print("-" * 70)
    print("Session ended.")

if __name__ == "__main__":
    asyncio.run(main())