"""Utility functions for file handling and JSON processing."""

import json
import re


def read_text_file(file_path: str) -> str:
    """Read and return the contents of a text file.

    Args:
        file_path: Path to the text file to read.

    Returns:
        The file contents as a string.
    """
    with open(file_path, encoding="utf-8") as file:
        return file.read()


def save_json_string_to_file(json_string: str, file_path: str) -> None:
    """Save a JSON string to a file.

    Args:
        json_string: The JSON content to save.
        file_path: Path where the file should be saved.
    """
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(json_string)


def extract_json_from_string(input_string: str) -> dict | None:
    """Extract and parse JSON from a string that may contain markdown code blocks.

    Handles strings that may be wrapped in ```json...``` markdown code blocks.

    Args:
        input_string: The string potentially containing JSON.

    Returns:
        The parsed JSON as a dictionary, or None if parsing fails.
    """
    try:
        # Remove markdown code block markers if present
        if input_string.startswith("```json"):
            input_string = re.sub(r"^```json\s*|\s*```$", "", input_string, flags=re.DOTALL)

        # Parse the JSON string
        json_object = json.loads(input_string)
        return json_object
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return None
