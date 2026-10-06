import os
import json
import google.generativeai as genai


# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-1.5-flash")


def generate_outline(user_prompt: str) -> list:
    """
    Generate a structured 5-panel comic outline
    using the Gemini Flash model.
    """

    prompt = f"""
You are a professional AI comic planner.

Create a 5-panel comic outline based on this story idea:

{user_prompt}

Return ONLY valid JSON.
Do not include markdown or explanations.

Each panel must contain:
- panel
- title
- scene_description
- image_prompt

Return exactly 5 panels in this format:

[
  {{
    "panel": 1,
    "title": "Title",
    "scene_description": "Scene description",
    "image_prompt": "Image generation prompt"
  }}
]
"""

    try:
        response = model.generate_content(prompt)
        output_text = response.text.strip()

        # Remove markdown JSON formatting if Gemini adds it
        if output_text.startswith("```json"):
            output_text = output_text.replace("```json", "", 1)
            output_text = output_text.replace("```", "")
        elif output_text.startswith("```"):
            output_text = output_text.replace("```", "")

        output_text = output_text.strip()

        panel_data = json.loads(output_text)

        # Validate output
        if not isinstance(panel_data, list):
            raise ValueError("Gemini response is not a list.")

        for panel in panel_data:
            required_keys = [
                "panel",
                "title",
                "scene_description",
                "image_prompt"
            ]

            if not isinstance(panel, dict):
                raise ValueError("Invalid panel format.")

            for key in required_keys:
                if key not in panel:
                    raise ValueError(f"Missing key: {key}")

        return panel_data

    except json.JSONDecodeError:
        print("Invalid JSON returned by Gemini.")
        return []

    except Exception as e:
        print(f"Error generating comic outline: {e}")
        return []vvv
