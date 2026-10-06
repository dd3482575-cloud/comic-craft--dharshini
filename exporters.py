import os
from datetime import datetime
from fpdf import FPDF

EXPORT_FOLDER = "static/exports"
os.makedirs(EXPORT_FOLDER, exist_ok=True)


def save_pdf(layout):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    for panel in layout:
        image_path = panel.get("image_path", "")
        story_text = panel.get("text", "")

        pdf.add_page()

        # Panel title
        pdf.set_font("Arial", "", 14)
        pdf.cell(0, 10, panel.get("title", "Comic Panel"), ln=True, align="C")

        # Image
        y_image = 30
        image_height = 100
        spacing_after_image = 15

        if image_path and os.path.exists(image_path):
            pdf.image(
                image_path,
                x=10,
                y=y_image,
                w=pdf.w - 20,
                h=image_height
            )
        else:
            pdf.set_y(y_image)
            pdf.multi_cell(0, 10, f"Image missing: {image_path}")

        # Story text
        pdf.set_y(y_image + image_height + spacing_after_image)

        story_lines = story_text.strip().splitlines()

        if story_lines and story_lines[0].strip().lower().startswith("**panel"):
            story_lines = story_lines[1:]

        cleaned_text = "\n".join(story_lines).strip()

        pdf.multi_cell(0, 10, cleaned_text)

    # Save PDF
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"comic_{timestamp}.pdf"
    pdf_path = os.path.join(EXPORT_FOLDER, filename)

    pdf.output(pdf_path)

    return pdf_path
