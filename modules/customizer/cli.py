import asyncio
import logging

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .agents import root_agent

logger = logging.getLogger(__name__)


async def main():
    """Run an interactive terminal dialogue with the recipe modifier agent."""

    logger.info("=" * 70)
    logger.info("MINECRAFT RECIPE MODIFIER AGENT - Interactive Test")
    logger.info("=" * 70)
    logger.info("This agent can help you create custom Minecraft recipes.")
    logger.info("Type 'quit' or 'exit' to end the conversation.")

    USER_ID = "default"

    session_service = InMemorySessionService()
    runner = Runner(agent=root_agent, app_name="default", session_service=session_service)

    try:
        session = await session_service.create_session(
            app_name="default", user_id=USER_ID, session_id="default"
        )
    except Exception:
        session = await session_service.get_session(
            app_name="default", user_id=USER_ID, session_id="default"
        )

    session_id = session.id
    logger.info("Session started (ID: %s)", session_id)
    logger.info("-" * 70)

    while True:
        try:
            user_input = input("\nYou: ").strip()

            if user_input.lower() in ["quit", "exit", "q"]:
                logger.info("Ending session. Goodbye!")
                break

            if not user_input:
                continue

            print("\nAgent: ", end="", flush=True)

            query = types.Content(role="user", parts=[types.Part(text=user_input)])

            async for event in runner.run_async(
                user_id=USER_ID, session_id=session_id, new_message=query
            ):
                if event.content and event.content.parts:
                    if event.content.parts[0].text != "None" and event.content.parts[0].text:
                        print(event.content.parts[0].text, end="", flush=True)

            print()

        except KeyboardInterrupt:
            logger.info("Interrupted by user. Ending session.")
            break
        except Exception as e:
            logger.error("Error: %s", e)
            logger.info("Continuing session...")

    logger.info("-" * 70)
    logger.info("Session ended.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    asyncio.run(main())
