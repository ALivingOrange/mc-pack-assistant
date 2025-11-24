import sys
import os
import platform

def ensure_environment(env_name="conda-env"):
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

    current_exe = os.path.normpath(sys.executable)
    target_python = os.path.normpath(target_python)

    if current_exe != target_python:
        print(f"Switching to local environment: {env_name}...")
        
        # Use os.execv to replace the current process with the new one
        # This keeps the PID the same and passes all arguments forward
        os.execv(target_python, [target_python, __file__] + sys.argv[1:])

ensure_environment("conda-env")

# from modules import customizer
import gradio as gr

def toggle_window(current_state):
    new_state = not current_state
    return new_state, gr.update(visible=new_state)

def process_message(user_input):
    # Placeholder for AI agent interaction
    return f"You said: {user_input}"

with gr.Blocks() as demo:
    window_state = gr.State(False)
    modifier_btn = gr.Button("Recipe Modifier")

    with gr.Row(visible=False) as modifier_window:
        with gr.Column():
            gr.Markdown("### Recipe Modifier")
            
            user_input = gr.Textbox(
                label="Your message",
                placeholder="Enter your message here...",
                lines=1
            )
            
            submit_btn = gr.Button("Submit")
            
            output = gr.Textbox(
                label="Response",
                lines=5,
                interactive=False
            )
            
            # Button click handler
            submit_btn.click(
                fn=process_message,
                inputs=user_input,
                outputs=output
            )
            
            # Enter key handler
            user_input.submit(
                fn=process_message,
                inputs=user_input,
                outputs=output
            )

    modifier_btn.click(
        fn=toggle_window,
        inputs=window_state,
        outputs=[window_state, modifier_window]
    )

if __name__ == "__main__":
    demo.launch()