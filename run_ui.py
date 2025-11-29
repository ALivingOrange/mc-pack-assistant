import sys
import os
import platform
import asyncio
from typing import Optional, Tuple, AsyncGenerator, Any

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
    else: # Linux or Mac
        target_python = os.path.join(env_path, "bin", "python")

    if not os.path.exists(target_python):
        print(f"Error: Could not find Conda environment at: {target_python}. Do you need to run the install script?")
        sys.exit(1)

    else:
        current_exe = os.path.normpath(sys.executable)
        target_python = os.path.normpath(target_python)

        if current_exe != target_python:
            print(f"Switching to local environment: {env_name}...")
            os.execv(target_python, [target_python, __file__] + sys.argv[1:])

ensure_environment("conda-env")

# ===== Initialization ========================================================

import gradio as gr
from modules.customizer import root_agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

if not os.path.exists("test.txt"):
    try:
        with open("test.txt", 'x') as file:
            file.write("ServerEvents.recipes(event =>{\n\n\n})")
        print("Created default test.txt")
    except Exception as e:
        print(f"Error creating test.txt: {e}")
else:
    print("Found existing test.txt")


# ===== Session Logic =========================================================

USER_ID: str = "default"
session_service = InMemorySessionService()
runner = Runner(agent=root_agent, app_name="default", session_service=session_service)


async def process_message(
    user_input: str, 
    current_session_id: Optional[str]
) -> AsyncGenerator[Tuple[str, str], None]:
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
        print(f"Active session: {current_session_id}")

    # --- Agent Query ---
    query = types.Content(role="user", parts=[types.Part(text=user_input)])
    
    accumulated_response: str = ""
    
    try:
        # Run the agent with streaming
        async for event in runner.run_async(
            user_id=USER_ID, 
            session_id=current_session_id, 
            new_message=query
        ):
            if event.content and event.content.parts:
                part_text = event.content.parts[0].text
                if part_text and part_text != "None":
                    accumulated_response += part_text
                    yield accumulated_response, current_session_id
                    
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(error_msg)
        yield error_msg, current_session_id

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

# ===== GUI ===================================================================

def toggle_window(current_state: bool) -> Tuple[bool, dict]:
    new_state = not current_state
    return new_state, gr.update(visible=new_state)

with gr.Blocks() as demo:
    with gr.Accordion("Settings / API Key", open=False):
            gr.Markdown("Enter your Gemini API Key below if it is not already set.")
            with gr.Row():
                api_key_input = gr.Textbox(
                    label="Gemini API Key", 
                    type="password", 
                    placeholder="key go here...",
                    scale=4
                )
                save_key_btn = gr.Button("Save Key", scale=1)
            
            save_status = gr.Label(label="Status", show_label=False)

            save_key_btn.click(
                fn=save_api_key,
                inputs=api_key_input,
                outputs=save_status
            )

    session_state = gr.State(value=None)
    window_state = gr.State(False)
    modifier_btn = gr.Button("Recipe Modifier")

    with gr.Row(visible=False) as modifier_window:
        with gr.Column():
            gr.Markdown("### Recipe Modifier")
            
            user_input = gr.Textbox(
                label="Your message",
                placeholder="Enter instructions for the recipe agent...",
                lines=1
            )
            
            submit_btn = gr.Button("Submit")
            
            output = gr.Textbox(
                label="Response",
                lines=10,
                interactive=False,
                autoscroll=True
            )
            
            # Button click handler
            submit_btn.click(
                fn=process_message,
                inputs=[user_input, session_state], # Pass input and current session ID
                outputs=[output, session_state]     # Update output and save session ID
            )
            
            # Enter key handler
            user_input.submit(
                fn=process_message,
                inputs=[user_input, session_state],
                outputs=[output, session_state]
            )

    modifier_btn.click(
        fn=toggle_window,
        inputs=window_state,
        outputs=[window_state, modifier_window]
    )

if __name__ == "__main__":
    demo.queue().launch()