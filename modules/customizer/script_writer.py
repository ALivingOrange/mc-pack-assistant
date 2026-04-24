from .config import OUTPUT_PATH


def append_to_script(lines_to_add: list[str]) -> dict:
    """Append lines to the KubeJS output script, preserving the trailing `})`.

    Reads OUTPUT_PATH, strips the closing `})` line, appends lines_to_add,
    re-appends `})`, and writes back.

    Args:
        lines_to_add: lines (each with its own newline(s) as needed) to insert
            before the closing `})`.

    Returns:
        {"status": "success"} on success, or
        {"status": "error", "error_message": str} on I/O failure.
    """
    try:
        with open(OUTPUT_PATH) as file:
            lines: list[str] = file.readlines()
    except OSError as e:
        return {"status": "error", "error_message": f"Error reading file: {e}"}

    if lines:
        lines = lines[:-1]

    lines.extend(lines_to_add)
    lines.append("})")

    try:
        with open(OUTPUT_PATH, "w") as file:
            file.writelines(lines)
    except OSError as e:
        return {"status": "error", "error_message": f"Error writing file: {e}"}

    return {"status": "success"}
