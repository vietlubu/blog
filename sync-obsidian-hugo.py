import os
import re
import shutil
import subprocess
import datetime
import sys
from urllib.parse import unquote
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Paths
obsidian_posts_dir = os.environ.get("OBSIDIAN_POSTS_DIR", "")
hugo_posts_dir = os.environ.get("HUGO_POSTS_DIR", "")
obsidian_attachments_dir = os.environ.get('OBSIDIAN_ATTACHMENTS_DIR', "")
hugo_static_images_dir = os.environ.get("HUGO_STATIC_IMAGES_DIR", "")

start_time = datetime.datetime.now()
print(f"Sync started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

if not obsidian_posts_dir or not hugo_posts_dir or not obsidian_attachments_dir or not hugo_static_images_dir:
    print("Error: Required environment variables are not set.")
    print(f"OBSIDIAN_POSTS_DIR: {obsidian_posts_dir}")
    print(f"HUGO_POSTS_DIR: {hugo_posts_dir}")
    print(f"OBSIDIAN_ATTACHMENTS_DIR: {obsidian_attachments_dir}")
    print(f"HUGO_STATIC_IMAGES_DIR: {hugo_static_images_dir}")
    exit(1)

# Step 1: Synchronize posts from Obsidian to Hugo using rsync (external command)
def sync_posts(specific_file=None):
    if specific_file:
        print(f"Synchronizing specific file: {specific_file}")
        source_file = os.path.join(obsidian_posts_dir, specific_file)
        dest_file = os.path.join(hugo_posts_dir, specific_file)

        # Ensure the destination directory exists
        os.makedirs(os.path.dirname(dest_file), exist_ok=True)

        if not os.path.exists(source_file):
            print(f"Error: Source file {source_file} does not exist.")
            return False

        try:
            rsync_command = ["rsync", "-av", source_file, dest_file]
            result = subprocess.run(rsync_command, capture_output=True, text=True)

            if result.returncode == 0:
                print("File sync successful!")
                print(result.stdout)
                return [dest_file]  # Return list of synced files
            else:
                print(f"File sync failed with code {result.returncode}")
                print(f"Error: {result.stderr}")
                return False
        except Exception as e:
            print(f"Error running rsync for specific file: {e}")
            return False
    else:
        print("Synchronizing all posts from Obsidian to Hugo...")
        try:
            rsync_command = ["rsync", "-av", "--delete", obsidian_posts_dir, hugo_posts_dir]
            result = subprocess.run(rsync_command, capture_output=True, text=True)

            if result.returncode == 0:
                print("Sync successful!")
                print(result.stdout)
                return True  # Return True for full sync
            else:
                print(f"Sync failed with code {result.returncode}")
                print(f"Error: {result.stderr}")
                return False
        except Exception as e:
            print(f"Error running rsync: {e}")
            return False

# Step 2: Process images in the posts
def process_images(files_to_process=None):
    print("\nProcessing images in posts...")

    # Ensure directories exist
    for directory in [hugo_posts_dir, hugo_static_images_dir]:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")

    # If specific files were provided, process only those files
    if files_to_process and isinstance(files_to_process, list):
        file_list = files_to_process
    else:
        # Process all markdown files in the Hugo posts directory
        file_list = []
        for root, _, files in os.walk(hugo_posts_dir):
            for filename in files:
                if filename.endswith(".md"):
                    file_list.append(os.path.join(root, filename))

    for filepath in file_list:
        if os.path.exists(filepath) and filepath.endswith(".md"):
            print(f"Processing file: {filepath}")
            with open(filepath, "r") as file:
                content = file.read()

            # Find all image links in Obsidian format ![[image.png]]
            images = re.findall(r'!\[\[(.*?\.png)\]\]', content)

            print(f"Found {len(images)} images: {images}")

            # Replace image links and copy images
            for image in images:
                # Replace Obsidian format with Markdown format
                original_pattern = f'![[{image}]]'
                markdown_image = f'![{image}](/images/{image.replace(" ", "%20")})'
                content = content.replace(original_pattern, markdown_image)

                # Try to find and copy the image
                # Check both with URL encoding and without
                decoded_image = unquote(image)

                image_source = os.path.join(obsidian_attachments_dir, image)
                decoded_source = os.path.join(obsidian_attachments_dir, decoded_image)

                print(f"Looking for image at: {image_source}")
                print(f"Or at decoded path: {decoded_source}")

                if os.path.exists(image_source):
                    print(f"Copying image: {image}")
                    shutil.copy(image_source, hugo_static_images_dir)
                elif os.path.exists(decoded_source):
                    print(f"Copying image: {decoded_image}")
                    shutil.copy(decoded_source, hugo_static_images_dir)
                else:
                    print(f"Warning: Could not find image: {image}")

            # Write the updated content back to the file
            with open(filepath, "w") as file:
                file.write(content)

# Main execution
if __name__ == "__main__":
    specific_file = None
    if len(sys.argv) > 1:
        specific_file = sys.argv[1].replace('\\', '')
        print(f"Processing specific file: {specific_file}")

    sync_result = sync_posts(specific_file)
    if sync_result:
        # If sync_result is a list, it contains specific files to process
        process_images(sync_result if isinstance(sync_result, list) else None)
        print("\nAll done! Blog posts synchronized and images processed.")
    else:
        print("\nSync failed. Image processing skipped.")
