import os

# Define the location for the API key.
KEY_FILE = "cache/.api_key"

def save_api_key():
    """
    Prompts the user for their Gemini API key and saves it to a local file.
    """
    # Check if the key file already exists
    if os.path.exists(KEY_FILE):
        overwrite = input(
            f"An API key file ('{KEY_FILE}') already exists.\n"
            "Do you want to overwrite it? (y/n): "
        ).strip().lower()
        if overwrite != 'y':
            print("Operation cancelled. Existing key file was not changed.")
            return

    # Prompt the user for the key
    api_key = input("Please enter your Gemini API key: ").strip()

    if not api_key:
        print("No API key entered. Exiting.")
        return

    try:
        # Write the key to the file
        with open(KEY_FILE, 'w') as f:
            f.write(api_key)
        
        print(f"\nSuccess! API key has been saved to {KEY_FILE}")

    except IOError as e:
        print(f"\nError: Could not write to file {KEY_FILE}.")
        print(f"Details: {e}")

if __name__ == "__main__":
    save_api_key()