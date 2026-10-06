import os
import json
import google.generativeai as genai


# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-1.5-pro")


def generate_story(panel_outline: list) -> list:
    """
    Generate comic story narration and dialogue
    based on the panel outline.
    """

    prompt = f"""
You are a professional comic story writer.

Create narration and dialogue for each panel
based on the following comic panel outline:

{json.dumps(panel_outline, indent=2)}

Return ONLY valid JSON.

For every panel include:
- panel
- narration
- dialogue

Return the result as a JSON list.
"""

    try:
        response = model.generate_content(prompt)
        output_text = response.text.strip()

        # Remove markdown JSON formatting
        if output_text.startswith("```json"):
            output_text = output_text.replace("```json", "", 1)
            output_text = output_text.replace("```", "")
        elif output_text.startswith("```"):
            output_text = output_text.replace("```", "")

        output_text = output_text.strip()

        story_data = json.loads(output_text)

        if not isinstance(story_data, list):
            raise ValueError("Gemini response is not a list.")

        for panel in story_data:
            if not isinstance(panel, dict):
                raise ValueError("Invalid panel format.")

            required_keys = ["panel", "narration", "dialogue"]

            for key in required_keys:
                if key not in panel:
                    raise ValueError(f"Missing key: {key}")

        return story_data

    except json.JSONDecodeError:
        print("Invalid JSON returned by Gemini.")
        return []

    except Exception as e:
        print(f"Error generating comic story: {e}")
        return []
