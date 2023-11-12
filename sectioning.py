from PIL import Image, ImageDraw, ImageFont
import PIL
import matplotlib.pyplot as plt


def outline_sections_on_image(original_image, section_dicts, indices=None, save=False, save_path="outlined_image.png", outline_width=5):
    """
    Outlines the section(s) of the original image specified by the indices in the section dictionary
    with a red rectangle, drawn inward. Optionally saves the image if 'save' is True.

    :param original_image: The original PIL Image object.
    :param section_dicts: A dictionary containing section data.
    :param indices: A list of indices for the sections to be outlined. If None, outlines all sections.
    :param save: Boolean, whether to save the image to a file.
    :param save_path: The path where the outlined image will be saved, if save is True.
    :param outline_width: The width of the outline.
    """

    # Create a copy of the original image to preserve it
    image_copy = original_image.copy()

    if indices is None:
        indices = range(len(section_dicts))
    elif isinstance(indices, str):
        indices = [int(indices)]  # Convert string to list of one integer

    # Calculate the encompassing box for the selected indices
    min_left = min(section_dicts[f'section_{i}']['global_box'][0] for i in indices)
    min_upper = min(section_dicts[f'section_{i}']['global_box'][1] for i in indices)
    max_right = max(section_dicts[f'section_{i}']['global_box'][2] for i in indices)
    max_lower = max(section_dicts[f'section_{i}']['global_box'][3] for i in indices)

    # Adjust the box to draw the outline inward
    inward_box = (min_left + outline_width, min_upper + outline_width, max_right - outline_width, max_lower - outline_width)

    # Draw a red rectangle outline on the copied image
    draw = ImageDraw.Draw(image_copy)
    draw.rectangle(inward_box, outline="red", width=outline_width)

    # Display the copied image
    plt.imshow(image_copy)
    plt.axis('off')  # Turn off axis numbers
    plt.show()

    # Save the modified image to the save_path if requested
    if save:
        image_copy.save(save_path)

    return image_copy



def split_image_with_gaps(input_data, indices=[], output_path=None, save=False):

    gap_size = 10  # Size of the green gap
    border_size = 5  # Size of the black border

    if isinstance(input_data, Image.Image):
        # It's the original image
        image = input_data
        width, height = image.size
        global_offset = (0, 0)  # No offset for the original image
    elif isinstance(input_data, dict):
        # It's a section dictionary
        #image = input_data['image']
        #width = input_data['box'][2] - input_data['box'][0]
        #height = input_data['box'][3] - input_data['box'][1]
        #global_offset = input_data['global_offset']
        min_left = min(input_data[f'section_{i}']['global_box'][0] for i in indices)
        min_upper = min(input_data[f'section_{i}']['global_box'][1] for i in indices)
        max_right = max(input_data[f'section_{i}']['global_box'][2] for i in indices)
        max_lower = max(input_data[f'section_{i}']['global_box'][3] for i in indices)
        width = max_right - min_left
        height = max_lower - min_upper
        global_offset = (min_left, min_upper)

        image = Image.new('RGB', (width, height))
        for i in range(3):  # Assuming 3x3 grid
            for j in range(3):
                section_key = f'section_{i * 3 + j}'
                if section_key in input_data:
                    section = input_data[section_key]
                    section_global_box = section['global_box']

                    # Check if the section is within the encompassing box
                    if (section_global_box[0] >= min_left and
                            section_global_box[1] >= min_upper and
                            section_global_box[2] <= max_right and
                            section_global_box[3] <= max_lower):
                        # Calculate position on the new canvas
                        pos_x = section_global_box[0] - min_left
                        pos_y = section_global_box[1] - min_upper

                        # Paste the section image onto the canvas
                        image.paste(section['image'], (pos_x, pos_y))

        #global_offset = input_data['global_offset']
    else:
        raise ValueError("Input data is neither an image nor a section dictionary.")

    sections_dict = {}
    section_width, section_height = width // 3, height // 3

    # Calculate the size of the new image with green gaps and black borders around each section
    new_width = (section_width + border_size * 2) * 3 + gap_size * 3
    new_height = (section_height + border_size * 2) * 3 + gap_size * 3
    new_image = Image.new('RGB', (new_width, new_height), 'green')

    try:
        font_size = min(section_width, section_height) // 2
        font = ImageFont.truetype("./arial.ttf", font_size)
        print("Font loaded successfully.")
    except IOError:
        print("Failed to load the font.")

    # Split the image into sections
    for i in range(3):
        for j in range(3):
            # Calculate the local box within the parent image
            local_box = (
                section_width * j,
                section_height * i,
                section_width * (j + 1),
                section_height * (i + 1)
            )
            # Crop the section from the parent image using the local box
            section_image = image.crop(local_box)

            # Calculate the global box based on the local box and global offset
            global_box = (
                global_offset[0] + local_box[0],
                global_offset[1] + local_box[1],
                global_offset[0] + local_box[2],
                global_offset[1] + local_box[3]
            )

            section_key = f'section_{i * 3 + j}'
            sections_dict[section_key] = {
                'box': local_box,  # The box within the current image context
                'global_box': global_box,  # The box within the original image context
                'image': section_image,
                'global_offset': (global_box[0], global_box[1])  # This becomes the new offset for subsections
            }

            # Calculate the position for the bordered section in the new image
            pos_x = gap_size + (border_size + section_width + gap_size) * j
            pos_y = gap_size + (border_size + section_height + gap_size) * i

            # Create a bordered section
            bordered_section = Image.new('RGBA', (section_width + border_size * 2, section_height + border_size * 2), 'black')
            bordered_section.paste(section_image, (border_size, border_size))

            text_layer = Image.new('RGBA', bordered_section.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(text_layer)
            section_number = str(i * 3 + j)
            text_width = draw.textlength(section_number, font=font)
            text_height = font.size
            text_x = (border_size + section_width + border_size - text_width) // 2
            text_y = (border_size + section_height + border_size - text_height) // 2
            outline_color = 'black'
            outline_width = 2  # The thickness of the outline

            # Draw the outline by drawing the text in the outline color at multiple offsets
            for offset in [(-outline_width, -outline_width), (-outline_width, outline_width),
                           (outline_width, -outline_width), (outline_width, outline_width),
                           (0, -outline_width), (0, outline_width),
                           (-outline_width, 0), (outline_width, 0)]:
                draw.text((text_x + offset[0], text_y + offset[1]), section_number, font=font, fill=outline_color)

            draw.text((text_x, text_y), section_number, fill=(255, 0, 0, 100), font=font)  # Semi-transparent red text
            # Paste the bordered section into the new image
            bordered_section.alpha_composite(text_layer)

            # Now paste the composited bordered_section onto the main image
            new_image.paste(bordered_section, (pos_x, pos_y), bordered_section)

    # Save the output image if requested
    if save and output_path:
        if not output_path.lower().endswith('.png'):
            output_path += '.png'
        new_image.save(output_path)
    return sections_dict, new_image if save else sections_dict




