import asyncio
import logging
import os
import platform
import subprocess
import sys
from collections.abc import AsyncGenerator

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


# ===== Environment ===========================================================
def ensure_environment(env_name: str = "conda-env") -> None:
    """
    Checks if the script is running via the python interpreter in the
    sibling folder. If not, re-launches the script using that interpreter.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, env_name)

    if platform.system() == "Windows":
        target_python = os.path.join(env_path, "python.exe")
    else:  # Linux or Mac
        target_python = os.path.join(env_path, "bin", "python")

    if not os.path.exists(target_python):
        logger.error(
            "Could not find Conda environment at: %s. Do you need to run the install script?",
            target_python,
        )
        sys.exit(1)

    else:
        current_exe = os.path.normpath(sys.executable)
        target_python = os.path.normpath(target_python)

        if current_exe != target_python:
            logger.info("Switching to local environment: %s...", env_name)
            os.execv(target_python, [target_python, __file__] + sys.argv[1:])


ensure_environment("conda-env")

# ===== Initialization ========================================================

import gradio as gr  # noqa: E402  (imports follow ensure_environment re-exec)
from google.adk.runners import Runner  # noqa: E402
from google.adk.sessions import InMemorySessionService  # noqa: E402
from google.genai import types  # noqa: E402

from modules.customizer import root_agent  # noqa: E402
from modules.pipeline import extract_item_ids, extract_recipes_from_log  # noqa: E402

# ===== Session Logic =========================================================

USER_ID: str = "default"
session_service = InMemorySessionService()
runner = Runner(agent=root_agent, app_name="default", session_service=session_service)


async def process_message(
    user_input: str, current_session_id: str | None
) -> AsyncGenerator[tuple[str, str], None]:
    """
    Async generator that handles the agent interaction.

    Args:
        user_input: The text string from the user.
        current_session_id: The ID stored in gr.State.

    Yields:
        Tuple[str, str]: (updated_response_text, updated_session_id)
    """
    if not user_input or not user_input.strip():
        yield "", current_session_id if current_session_id else ""
        return

    # --- Session Management ---
    if current_session_id is None:
        try:
            session = await session_service.create_session(
                app_name="default", user_id=USER_ID, session_id="default"
            )
        except Exception:
            # Fallback to get_session if create fails
            session = await session_service.get_session(
                app_name="default", user_id=USER_ID, session_id="default"
            )
        current_session_id = session.id
        logger.info("Active session: %s", current_session_id)

    # --- Agent Query ---
    query = types.Content(role="user", parts=[types.Part(text=user_input)])

    accumulated_response: str = ""

    try:
        # Run the agent with streaming
        async for event in runner.run_async(
            user_id=USER_ID, session_id=current_session_id, new_message=query
        ):
            if event.content and event.content.parts:
                part_text = event.content.parts[0].text
                if part_text and part_text != "None":
                    accumulated_response += part_text
                    yield accumulated_response, current_session_id

    except Exception as e:
        error_msg = f"Error: {str(e)}"
        logger.exception("Agent run failed")
        yield error_msg, current_session_id


# ===== Other logic ===========================================================


def save_api_key(api_key: str):
    if not api_key.strip():
        return "Error: Key cannot be empty."

    try:
        os.makedirs("cache", exist_ok=True)

        key_file = "cache/.api_key"
        with open(key_file, "w") as f:
            f.write(api_key.strip())
        return "API Key saved. You must restart the UI for this to take effect."
    except Exception as e:
        return f"Error saving key: {str(e)}"


async def run_extractor():
    try:
        output_file = await asyncio.to_thread(extract_item_ids)
        return f"Extractor finished. Wrote {output_file}."
    except Exception as e:
        logger.exception("Extractor failed")
        return f"Error running extractor: {e}"


def _recipe_server_run_blocking():
    """
    Runs the Minecraft server, waits for the recipe dump trigger,
    stops the server, and runs the catcher script.
    """
    server_dir = os.path.join(os.getcwd(), "server")

    java_binary = "java.exe" if platform.system() == "Windows" else "java"
    jre_path = os.path.join(os.getcwd(), "jre", "bin", java_binary)

    if not os.path.exists(jre_path):
        return f"Error: Portable Java not found at {jre_path}"

    server_command = [jre_path, "-Xmx4G", "-jar", "server.jar", "nogui"]

    trigger_prefix = "AGENTSYS_RECIPE_DUMP_END::"
    recipe_count = 0
    log_capture = []

    try:
        log_capture.append("Starting server...")
        server_process = subprocess.Popen(
            server_command,
            cwd=server_dir,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        found_trigger = False

        for line in server_process.stdout:
            sys.stdout.write(line)

            if trigger_prefix in line:
                found_trigger = True
                try:
                    parts = line.strip().split("::")
                    if len(parts) > 1:
                        recipe_count = parts[1]
                except Exception:
                    recipe_count = "Unknown"

                log_capture.append(f"Trigger detected! Recipes dumped: {recipe_count}")
                log_capture.append("Sending 'stop' command...")

                server_process.stdin.write("/stop\n")
                server_process.stdin.flush()
                break

        server_process.wait()
        log_capture.append("Server shutdown complete.")

        if not found_trigger:
            return "Server stopped without seeing the trigger phrase."

    except Exception as e:
        return f"Error running server: {str(e)}"

    try:
        log_capture.append("Extracting recipes from server log...")
        count = extract_recipes_from_log()
        log_capture.append(f"Catcher finished. Extracted {count} recipes.")
    except FileNotFoundError as e:
        log_capture.append(f"Catcher failed: {e}")
    except Exception as e:
        log_capture.append(f"Error running catcher: {e}")

    return "\n".join(log_capture)


async def recipe_server_run():
    return await asyncio.to_thread(_recipe_server_run_blocking)


# ===== GUI ===================================================================


def toggle_window(current_state: bool) -> tuple[bool, dict]:
    new_state = not current_state
    return new_state, gr.update(visible=new_state)


with gr.Blocks() as demo:
    with gr.Accordion("Setup", open=False):
        gr.Markdown("### Run each of these, then restart the UI before first use.")
        gr.Markdown("Enter your Gemini API Key below if it is not already set.")
        with gr.Row():
            api_key_input = gr.Textbox(
                label="Gemini API Key", type="password", placeholder="key go here...", scale=4
            )
            save_key_btn = gr.Button("Save Key", scale=1)

        save_status = gr.Label(label="Status", show_label=False)

        save_key_btn.click(fn=save_api_key, inputs=api_key_input, outputs=save_status)
        gr.Markdown("---")
        with gr.Row():
            gr.Markdown("Extract Item IDs for use in agent searches.")
            extractor_btn = gr.Button("Run Item ID Extractor", scale=1)
        extractor_status = gr.Textbox(label="Extractor Output", lines=1, interactive=False)
        gr.Markdown("---")
        with gr.Row():
            gr.Markdown("Run Server, Dump Recipes, & Catch Results")
            dump_btn = gr.Button("Run Recipe Dump Cycle", scale=1)

        dump_status = gr.Textbox(label="Dump Cycle Status", lines=6, interactive=False)

        dump_btn.click(fn=recipe_server_run, inputs=None, outputs=dump_status)

        extractor_btn.click(fn=run_extractor, inputs=None, outputs=extractor_status)

    session_state = gr.State(value=None)
    window_state = gr.State(False)
    modifier_btn = gr.Button("Recipe Modifier")

    with gr.Row(visible=False) as modifier_window:
        with gr.Column():
            gr.Markdown("### Recipe Modifier")

            user_input = gr.Textbox(
                label="Your message",
                placeholder="Enter instructions for the recipe agent...",
                lines=1,
            )

            submit_btn = gr.Button("Submit")

            output = gr.Textbox(label="Response", lines=10, interactive=False, autoscroll=True)

            # Button click handler
            submit_btn.click(
                fn=process_message,
                inputs=[user_input, session_state],  # Pass input and current session ID
                outputs=[output, session_state],  # Update output and save session ID
            )

            # Enter key handler
            user_input.submit(
                fn=process_message,
                inputs=[user_input, session_state],
                outputs=[output, session_state],
            )

    modifier_btn.click(
        fn=toggle_window, inputs=window_state, outputs=[window_state, modifier_window]
    )

if __name__ == "__main__":
    demo.queue().launch()
