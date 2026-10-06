def generate_image(prompt, filename=None):
    if not filename:
        filename = sanitize_filename(prompt)

    image = pipe(prompt).images[0]
    path = f"static/panels/{filename}"

    os.makedirs(os.path.dirname(path), exist_ok=True)
    image.save(path)

    return path
