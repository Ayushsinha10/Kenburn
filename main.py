import argparse
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

    image_width = 1920
    image_height = 1080

    # Create an image with a white background
    image = Image.new("RGB", (image_width, image_height), "white")
    draw = ImageDraw.Draw(image)


    original_font_size = 80
    new_font_size = original_font_size
    
    try:
        font = ImageFont.truetype("Roboto-Bold.ttf", new_font_size)
    except IOError:
        font = ImageFont.load_default()


    while True:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Check if the text fits within the image dimensions
        if text_width <= image_width and text_height <= image_height:
            break


        new_font_size -= 5
        font = ImageFont.truetype("Roboto-Bold.ttf", new_font_size)

    # Calculate the position to center the text
    text_position = (
        (image_width - text_width) // 2,
        (image_height - text_height) // 2
    )

    draw.text(text_position, text, font=font, fill="black")


    image.save(save_path)


# Depricated Function
def write_text_on_image(image_path, text, save_path):
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)


    original_font_size = 40  
    new_font_size = original_font_size * 20 
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
    

    draw.text(text_position, text, font=font, fill="white")


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
                   # write_text_on_image(save_path, description, save_path)
                    text_image_save_path = os.path.join(download_dir, 'DESC.jpg')
                    create_text_image(description, text_image_save_path)
                    os.utime('downloads/'+file_name)
           
        
        # Process tags if present
        if 'tags' in image_data:
         for tag_index, tag in enumerate(image_data['tags']):
        # Check if the context is 'feature'
          if tag.get('context') == 'feature':
            title = tag['title']
            if 'image' in tag and 'large' in tag['image']:
                tag_image_url = tag['image']['large']
                tag_file_name = f"{data['title']}_{index+1}_tag_{tag_index+1}_large.jpg"
                tag_save_path = os.path.join(download_dir, tag_file_name)
                
                # Download the tag image
                if download_image(tag_image_url, tag_save_path):
                    # Write title onto the image
                   # write_text_on_image(tag_save_path, title, tag_save_path)
                    text_image_file_name = f"{data['title']}_{index+1}_tag_{tag_index+1}_title.jpg"
                    text_image_save_path = os.path.join(download_dir, text_image_file_name)
                    create_text_image(title, text_image_save_path)
                    os.utime(tag_save_path)  # Update the modification time of the downloaded image file
            print(f"Title: {title}, Image URL: {tag_image_url}")
def pad_image_to_size(img, target_width, target_height):

    height, width = img.shape[:2]
    top = (target_height - height) // 2
    bottom = target_height - height - top
    left = (target_width - width) // 2
    right = target_width - width - left
    
    # Pad the image with black borders
    padded_img = cv2.copyMakeBorder(
        img,
        top, bottom, left, right,
        cv2.BORDER_CONSTANT,
        value=[0, 0, 0]  # Black color
    )
    return padded_img

def create_slideshow(image_folder, output_video_path, duration_per_image, pan, zoom, fade_duration=0.6, feature_fade_duration=2.0, fps=60):
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
        if img is None:
            print(f"Error loading image: {image_files[i]}")
            continue

        is_feature = "title" in image_files[i] or (i == 0)
        
        if not is_feature:
            if zoom and pan:
                # Zoom and pan effect combined
                initial_zoom_factor = 1
                final_zoom_factor = 1.5
                
                for j in range(int(fps * (duration_per_image/2))):
                    # Zoom effect
                    zoom_factor = initial_zoom_factor + (final_zoom_factor - initial_zoom_factor) * (j / (fps * duration_per_image))
                    zoomed_img = cv2.resize(img, None, fx=zoom_factor, fy=zoom_factor)
                    x_center, y_center = zoomed_img.shape[1] // 2, zoomed_img.shape[0] // 2
                    x1 = x_center - width // 2
                    y1 = y_center - height // 2
                    zoomed_img = zoomed_img[y1:y1 + height, x1:x1 + width]
                    
                    video.write(zoomed_img)

                    # Pan effect
                pan_start_x = 0
                pan_end_x = width - int(width * 0.9)  
                    
                for j in range(int(fps * (duration_per_image / 2))):  # The other half of the duration for panning
                    pan_x = int(pan_start_x + (pan_end_x - pan_start_x) * (j / (fps * (duration_per_image / 2))))
                    panned_img = zoomed_img[:, pan_x:pan_x + int(width * 0.8)]
                    panned_img = pad_image_to_size(panned_img, 1920, 1080)

                    video.write(panned_img)
            elif pan:
                # Pan effect only
                pan_start_x = 0
                pan_end_x = width - int(width * 0.8)  # Pan across 80% of the width
    
                for j in range(int(fps * duration_per_image)):
                  pan_x = int(pan_start_x + (pan_end_x - pan_start_x) * (j / (fps * duration_per_image)))
                  pan_x = max(0, min(pan_x, width - int(width * 0.8)))
                  panned_img = img[:, pan_x:pan_x + int(width * 0.8)]

                  panned_img = pad_image_to_size(panned_img, 1920, 1080)
        
                  video.write(panned_img)
            elif zoom:
                # Zoom effect only
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

            else:
                # No pan or zoom effect
                for j in range(int(fps * duration_per_image)):
                    video.write(img)
        
        else:
            # No zoom or pan effect for feature images
            for j in range(int(fps * duration_per_image)):
                video.write(img)
        
        if i < len(image_files) - 1:
            next_img = cv2.imread(image_files[i + 1])
            if next_img is None:
                print(f"Error loading next image: {image_files[i + 1]}")
                continue

            fade_duration_for_transition = feature_fade_duration if is_feature else fade_duration
            
            for k in range(int(fps * fade_duration_for_transition)):
                alpha = k / (fps * fade_duration_for_transition)
                
                if is_feature:
                    background_img = next_img
                    blended_img = cv2.addWeighted(background_img, alpha, img, 1 - alpha, 0)
                else:
                    # Normal fade transition
                    blended_img = cv2.addWeighted(img, 1 - alpha, next_img, alpha, 0)
                    
                video.write(blended_img)

    video.release()
    print(f"Video slideshow created at {output_video_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process images and create a slideshow video.")

    parser.add_argument("data_file_path", type=str, help="Path to the data file (e.g., 'data/FL70JZX.txt').")
    parser.add_argument("download_dir", type=str, help="Directory to save downloaded images (e.g., 'downloads').")
    parser.add_argument("output_video_path", type=str, help="Path to save the output slideshow video (e.g., 'slideshow.mp4').")
    parser.add_argument("duration_image", type=int, help="How long each image stays on frame in seconds(e.g, '1'').")
    parser.add_argument("--pan", action="store_true", help="Add pan effect to images.")
    parser.add_argument("--zoom", action="store_true", help="Add zoom effect to images.")

    args = parser.parse_args()

    # Verification checks
    if not os.path.isfile(args.data_file_path):
        print(f"Error: The data file '{args.data_file_path}' does not exist.")
        exit(1)

    if not os.path.isdir(args.download_dir):
        print(f"Warning: The download directory '{args.download_dir}' does not exist. Creating it now.")
        os.makedirs(args.download_dir)

    if not args.output_video_path.endswith('.mp4'):
        print("Error: The output video path must end with '.mp4'.")
        exit(1)




    main(args.data_file_path, args.download_dir)


    create_slideshow(args.download_dir, args.output_video_path, args.duration_image, args.pan, args.zoom)