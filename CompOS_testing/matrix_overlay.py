import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import os

def overlay_top_archetypes(image_path, top_archetypes, title):
    """
    Overlays the top archetypes on the matrix image and saves it as 'matrix_[title].png'.
    """

    # Convert list of lists to list of tuples (if needed)
    if isinstance(top_archetypes, list) and isinstance(top_archetypes[0], list):
        top_archetypes = [tuple(item) for item in top_archetypes]
        st.write("✅ Converted to tuples:", top_archetypes)  # Debug output

    # Load the image
    image = Image.open(image_path)

    # Define fixed positions for each archetype in the 4x4 matrix
    archetype_positions = {
        "Technologist": (70, 140), "Optimiser": (165, 140), "Globe-trotter": (260, 140), "Accelerator": (355, 140),
        "Value Seeker": (70, 233), "Expert": (165, 233), "Guardian": (260, 233), "Futurist": (355, 233),
        "Simplifier": (70, 328), "Personaliser": (165, 328), "Principled": (260, 328), "Collaborator": (355, 328),
        "Mentor": (70, 425), "Nurturer": (165, 425), "People’s Champion": (260, 425), "Eco Warrior": (355, 425),
    }

    # Create a drawing context
    draw = ImageDraw.Draw(image)

    # Try to load a font (if available), otherwise use default
    try:
        font = ImageFont.truetype("arial.ttf", 13)
    except IOError:
        font = ImageFont.load_default()

    # Draw blue tags with white text for the top archetypes
    for archetype, percentage in top_archetypes:
        if archetype in archetype_positions:
            x, y = archetype_positions[archetype]
            text = f"News - {percentage:.1f}%"

            # Get text bounding box for accurate size
            bbox = draw.textbbox((x, y), text, font=font)
            box_x1, box_y1, box_x2, box_y2 = bbox

            # Add padding around the text
            padding = 5
            box_x1 -= padding
            box_y1 -= padding
            box_x2 += padding
            box_y2 += padding

            # Draw blue rectangle (tag background)
            draw.rectangle([box_x1, box_y1, box_x2, box_y2], fill="blue", outline="blue")

            # Draw white text on top of the blue rectangle
            draw.text((x, y), text, fill="white", font=font)

    # Generate the output file name based on the title
    output_filename = f"matrix_{title}.png"
    image.save(output_filename, format="PNG")

    return output_filename  # Return the saved file path
