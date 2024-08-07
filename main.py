import os
import requests
import json
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def read_json_from_file(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def download_image(url, save_path):
    response = requests.get(url)
    if response.status_code == 200:
        with open(save_path, 'wb') as file:
            file.write(response.content)
        return True
    else:
        print(f"Failed to download image from {url}")
        return False



def create_text_image(text, save_path):
    # Load a font
    original_font_size = 40  # Original font size
    new_font_size = original_font_size * 20  # Increase font size by a factor of 20
    try:
        font = ImageFont.truetype("arial.ttf", new_font_size)
    except IOError:
        font = ImageFont.load_default()

    # Create a temporary image to calculate text size
    temp_image = Image.new("RGB", (1, 1))
    draw = ImageDraw.Draw(temp_image)
    
    # Calculate text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    image_width = 1920 # Add some padding
    image_height = 1080 # Add some padding

    # Create an image with white background
    image = Image.new("RGB", (image_width, image_height), "white")
    draw = ImageDraw.Draw(image)

    # Position for the text
    text_position = (
        (image_width - text_width) // 2,
        (image_height - text_height) // 2
    )

    # Add text to image
    draw.text(text_position, text, font=font, fill="black")

    # Save the image
    image.save(save_path)



def write_text_on_image(image_path, text, save_path):
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)

    # Load a font
    original_font_size = 40  # Original font size
    new_font_size = original_font_size * 20  # Increase font size by a factor of 20
    try:
        font = ImageFont.truetype("arial.ttf", new_font_size)
    except IOError:
        font = ImageFont.load_default()

    # Calculate text size and position
    text_size = draw.textbbox((0, 0), text, font=font)
    text_width = text_size[2] - text_size[0]
    text_height = text_size[3] - text_size[1]
    image_width, image_height = image.size

    # Padding around the text
    padding = 50  # Adjust padding as needed

    # Position for the background rectangle
    background_position = (
        (image_width - text_width - 2 * padding) // 2,
        (image_height - text_height - 2 * padding) // 2,
        (image_width + text_width + 2 * padding) // 2,
        (image_height + text_height + 2 * padding) // 2
    )
    
    # Draw background rectangle for text
    draw.rectangle(background_position, fill="black")

    # Position for the text
    text_position = (
        (image_width - text_width) // 2,
        (image_height - text_height) // 2
    )
    
    # Add text to image
    draw.text(text_position, text, font=font, fill="white")

    # Save the image
    image.save(save_path)

    print(f"Text '{text}' written to {save_path}")


# Main function to handle the downloading of images
def main(data_file_path, download_dir):
    # Read data from the JSON file
    data = read_json_from_file(data_file_path)
    
    # Create download directory if it doesn't exist
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    # Process each image entry
    for index, image_data in enumerate(data['images']):
        # Download the large image
        if 'large' in image_data:
            file_name = f"{data['title']}_{index+1}_large.jpg"
            save_path = os.path.join(download_dir, file_name)
            download_image(image_data['large'], save_path)
            if index == 0:
                    description = data.get('description', 'No Description')
                    write_text_on_image(save_path, description, save_path)
                    text_image_save_path = os.path.join(download_dir, 'DESC.jpg')
                    create_text_image(description, text_image_save_path)
                    os.utime('downloads/'+file_name)
           
        
        # Process tags if present
        if 'tags' in image_data:
            for tag_index, tag in enumerate(image_data['tags']):
                title = tag['title']
                if 'image' in tag and 'large' in tag['image']:
                    tag_image_url = tag['image']['large']
                    tag_file_name = f"{data['title']}_{index+1}_tag_{tag_index+1}_large.jpg"
                    tag_save_path = os.path.join(download_dir, tag_file_name)
                    
                    # Download the tag image
                    if download_image(tag_image_url, tag_save_path):
                        # Write title onto the image
                        write_text_on_image(tag_save_path, title, tag_save_path)
                        text_image_file_name = f"{data['title']}_{index+1}_tag_{tag_index+1}_title.jpg"
                        text_image_save_path = os.path.join(download_dir, text_image_file_name)
                        create_text_image(title, text_image_save_path)
                        tag_file_name = f"{data['title']}_{index+1}_tag_{tag_index+1}_large.jpg"
                        os.utime('downloads/'+tag_file_name)
                    print(f"Title: {title}, Image URL: {tag_image_url}")

def create_slideshow(image_folder, output_video_path, duration_per_image=1, fade_duration=0.6, fps=30):
    image_files = [os.path.join(image_folder, img) for img in os.listdir(image_folder) if img.endswith(('jpg', 'jpeg', 'png'))]
    image_files.sort(key=lambda x: os.path.getmtime(x), reverse=False)
    if not image_files:
        print("No images found in the directory.")
        return

    # Get the size of the first image
    first_image = cv2.imread(image_files[0])
    height, width, layers = first_image.shape

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

    for i in range(len(image_files)):
        img = cv2.imread(image_files[i])
        
        # Add Ken Burns effect by slightly zooming
        initial_zoom_factor = 1
        final_zoom_factor = 1.5
        for j in range(int(fps * duration_per_image)):
            zoom_factor = initial_zoom_factor + (final_zoom_factor - initial_zoom_factor) * (j / (fps * duration_per_image))
            zoomed_img = cv2.resize(img, None, fx=zoom_factor, fy=zoom_factor)
            x_center, y_center = zoomed_img.shape[1] // 2, zoomed_img.shape[0] // 2
            x1 = x_center - width // 2
            y1 = y_center - height // 2
            zoomed_img = zoomed_img[y1:y1 + height, x1:x1 + width]
            video.write(zoomed_img)

        # Fade-out effect for the current image
        if i < len(image_files) - 1:
            next_img = cv2.imread(image_files[i + 1])
            for k in range(int(fps * fade_duration)):
                alpha = k / (fps * fade_duration)
                blended_img = cv2.addWeighted(zoomed_img, 1 - alpha, next_img, alpha, 0)
                video.write(blended_img)
    
    video.release()
    print(f"Video slideshow created at {output_video_path}")

if __name__ == "__main__":
    data_file_path = 'data/FL70JZX.txt'
    download_dir = 'downloads'
    output_video_path = 'slideshow.mp4'
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
    main(data_file_path, download_dir)
    
    create_slideshow(download_dir, output_video_path)