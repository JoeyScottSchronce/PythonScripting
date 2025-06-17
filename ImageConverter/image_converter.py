import os
import tkinter as tk
from tkinter import filedialog
from PIL import Image
import logging
from pathlib import Path
import tkinterdnd2 as tkdnd
import math
import time

# Set up the main application window
root = tkdnd.TkinterDnD.Tk()
root.title("Image Converter")
root.configure(bg="#2B2B2B")  # Dark gray background

# Set window size and position near the top-right corner
window_width = 300
window_height = 200
offset = 50
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x_position = screen_width - window_width - offset
y_position = offset
root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

# Get the Downloads folder path
downloads_path = str(Path.home() / "Downloads")
output_folder = os.path.join(downloads_path, "Converted_Images")
os.makedirs(output_folder, exist_ok=True)

# Set up logging
log_file = os.path.join(output_folder, "log.txt")
logging.basicConfig(filename=log_file, level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger()

# Track conversion stats
total_files = 0
successful_conversions = 0
skipped_files = 0
total_size_removed = 0

def calculate_entropy(img):
    """Calculate image entropy to determine complexity for adaptive compression."""
    histogram = img.histogram()
    histogram_length = sum(histogram)
    if histogram_length == 0:
        return 0
    probabilities = [float(h) / histogram_length for h in histogram if h != 0]
    return -sum(p * math.log2(p) for p in probabilities)

def process_images(file_paths):
    global total_files, successful_conversions, skipped_files, total_size_removed
    total_files = len(file_paths)
    successful_conversions = 0
    skipped_files = 0
    total_size_removed = 0

    # Initialize status label
    status_label.config(text="Preparing...")
    root.update_idletasks()

    for i, file_path in enumerate(file_paths, 1):
        file_ext = os.path.splitext(file_path)[1].lower()

        # Skip if already WebP
        if file_ext == ".webp":
            logger.info(f"Skipped {file_path} (already WebP)")
            skipped_files += 1
            status_label.config(text=f"Processing:\n{i}/{total_files} {'image' if total_files == 1 else 'images'}")
            root.update_idletasks()
            time.sleep(0.01)  # Slight delay for visible updates
            continue

        # Check if file is a supported image format
        if file_ext not in [".png", ".jpg"]:
            logger.warning(f"Skipped imageteller {file_path} (unsupported image format)")
            skipped_files += 1
            status_label.config(text=f"Processing:\n{i}/{total_files} {'image' if total_files == 1 else 'images'}")
            root.update_idletasks()
            time.sleep(0.01)
            continue

        try:
            # Open image and get original size
            original_size = os.path.getsize(file_path) / 1024  # KB
            img = Image.open(file_path)

            # Optimize PNG inputs
            if file_ext == ".png":
                img.save("temp.png", optimize=True)
                img = Image.open("temp.png")

            # Convert to RGB if necessary
            if img.mode in ("RGBA", "LA"):
                img = img.convert("RGB")

            # Resize to max 1000px
            max_dimensions = (1000, 1000)
            img.thumbnail(max_dimensions, Image.Resampling.LANCZOS)

            # Determine compression settings based on entropy
            entropy = calculate_entropy(img)
            if entropy < 4.0:  # Low complexity (e.g., text, logos)
                quality = 60
                lossless = True
            else:  # High complexity (e.g., photos)
                quality = 75
                lossless = False

            output_filename = os.path.splitext(os.path.basename(file_path))[0] + ".webp"
            output_path = os.path.join(output_folder, output_filename)

            # Save as WebP with optimized settings
            save_params = {
                "format": "WEBP",
                "quality": quality if not lossless else 100,
                "lossless": lossless,
                "method": 6,  # Maximum compression effort
                "exif": b"",  # Strip EXIF metadata
                "icc_profile": None  # Strip ICC profile
            }
            img.save(output_path, **save_params)

            # Calculate size savings
            output_size = os.path.getsize(output_path) / 1024  # KB
            size_saved = original_size - output_size
            total_size_removed += size_saved

            logger.info(
                f"Successfully converted {file_path} to {output_path} (quality={quality}, lossless={lossless}, original={original_size:.1f}KB, output={output_size:.1f}KB, saved={size_saved:.1f}KB)")
            successful_conversions += 1

        except Exception as e:
            logger.error(f"Failed to convert {file_path}: {str(e)}")

        # Update status label with counter
        status_label.config(text=f"Processing:\n{i}/{total_files} {'image' if total_files == 1 else 'images'}")
        root.update_idletasks()
        time.sleep(0.01)  # Slight delay for visible updates

    # Show final status
    success_rate = (successful_conversions / total_files * 100) if total_files > 0 else 0
    status_text = f"Success: {successful_conversions}/{total_files}\nRemoved: {total_size_removed:.1f} KB"
    status_label.config(text=status_text)
    logger.info(status_text)

    # Clean up the temporary PNG file
    if os.path.exists("temp.png"):
        os.remove("temp.png")

def select_files():
    files = filedialog.askopenfilenames(
        title="Select Images",
        filetypes=[("Image files", "*.png *.jpg")]
    )
    if files:
        process_images(files)

def drop(event):
    # Handle dropped files
    file_paths = root.tk.splitlist(event.data)
    process_images(file_paths)

# UI Elements
frame = tk.Frame(root, bg="#2B2B2B")
frame.pack(pady=20)

instruction_label = tk.Label(frame, text="drop images here to convert\npng & jpg into webp",
                             bg="#2B2B2B", fg="#FFFFFF", font=("Arial", 12))
instruction_label.pack(pady=10)

select_button = tk.Button(frame, text="Select Images", command=select_files,
                          bg="#3C3F41", fg="#FFFFFF", font=("Arial", 10), activebackground="#4B4B4B")
select_button.pack(pady=10)

status_label = tk.Label(frame, text="", bg="#2B2B2B", fg="#FFFFFF", font=("Arial", 10))
status_label.pack(pady=10)

# Enable drag-and-drop
root.drop_target_register(tkdnd.DND_FILES)
root.dnd_bind('<<Drop>>', drop)

# Start the application
root.mainloop()