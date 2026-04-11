import base64
import io
import os
import shutil
import subprocess
import sys
import time
import tkinter as tk
from tkinter import filedialog
from urllib.parse import unquote, urlparse
from PIL import Image
import logging
from pathlib import Path
import tkinterdnd2 as tkdnd
import math

# Set up the main application window
root = tkdnd.TkinterDnD.Tk()
root.title("SVG Converter")
root.configure(bg="#2B2B2B")  # Dark gray background

# Set window size and position near the top-right corner
window_width = 720
window_height = 320
offset = 400
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

SUPPORTED_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".webp"})

# Track conversion stats
total_files = 0
successful_conversions = 0
total_original_kb = 0.0
total_output_kb = 0.0


def pick_root_folder() -> tuple[str, str]:
    """Pick a directory to use as conversion root. Returns (path or \"\", source).

    On Linux, Tk's askdirectory often returns the parent when the user opened a
    subfolder (GNOME/GTK quirk). Prefer zenity or kdialog.
    """
    title = "Select root folder (images in this folder and subfolders)"
    home = str(Path.home())

    if sys.platform.startswith("linux"):
        zenity = shutil.which("zenity")
        if zenity:
            try:
                r = subprocess.run(
                    [
                        zenity,
                        "--file-selection",
                        "--directory",
                        f"--title={title}",
                        f"--filename={home}{os.sep}",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=3600,
                )
                if r.returncode == 0:
                    line = (r.stdout or "").strip().split("\n", 1)[0].strip()
                    if line and os.path.isdir(line):
                        return (line, "zenity")
            except (OSError, subprocess.TimeoutExpired):
                pass

        kdialog = shutil.which("kdialog")
        if kdialog:
            try:
                r = subprocess.run(
                    [kdialog, "--getexistingdirectory", home, title],
                    capture_output=True,
                    text=True,
                    timeout=3600,
                )
                if r.returncode == 0:
                    line = (r.stdout or "").strip()
                    if line and os.path.isdir(line):
                        return (line, "kdialog")
            except (OSError, subprocess.TimeoutExpired):
                pass

    tk_path = filedialog.askdirectory(title=title, mustexist=True) or ""
    if sys.platform.startswith("linux"):
        logger.warning(
            "Select folder: zenity/kdialog unavailable; using Tk (may return parent folder on some GTK setups)."
        )
    return (tk_path, "tk")


def normalize_dnd_path(raw: str) -> str:
    p = raw.strip()
    if len(p) >= 2 and p[0] == "{" and p[-1] == "}":
        p = p[1:-1]
    if p.startswith("file:"):
        parsed = urlparse(p)
        p = unquote(parsed.path)
        if os.name == "nt" and len(p) >= 3 and p[0] == "/" and p[2] == ":":
            p = p[1:]
    p = os.path.normpath(p)
    if not os.path.isabs(p) and os.path.exists(p):
        p = os.path.abspath(p)
    return p


def resolve_directory_root(p: str) -> str:
    """Absolute, canonical directory to use as os.walk root (the chosen folder itself)."""
    if not os.path.isdir(p):
        return p
    return str(Path(p).resolve())


def batch_includes_folder(raw_paths: list[str]) -> bool:
    """True if any dropped/selected path is a directory (triggers in-place + delete originals)."""
    for raw in raw_paths:
        p = normalize_dnd_path(raw)
        if os.path.isdir(p):
            return True
    return False


def collect_image_paths(raw_paths: list[str]) -> list[str]:
    """Expand files and directories; recursively collect supported images (sorted)."""
    collected: list[str] = []
    for raw in raw_paths:
        p = normalize_dnd_path(raw)
        if not os.path.exists(p):
            logger.warning(f"Skipped missing path: {raw}")
            continue
        if os.path.isfile(p):
            ext = os.path.splitext(p)[1].lower()
            if ext in SUPPORTED_EXTENSIONS:
                collected.append(p)
            else:
                logger.warning(f"Skipped file {p} (unsupported image format)")
        elif os.path.isdir(p):
            root_dir = resolve_directory_root(p)
            for walk_root, _dirs, files in os.walk(root_dir):
                for name in files:
                    ext = os.path.splitext(name)[1].lower()
                    if ext in SUPPORTED_EXTENSIONS:
                        collected.append(os.path.join(walk_root, name))
        else:
            logger.warning(f"Skipped path {p} (not a file or directory)")
    return sorted(collected)

def calculate_entropy(img):
    """Calculate image entropy to determine complexity for adaptive compression."""
    histogram = img.histogram()
    histogram_length = sum(histogram)
    if histogram_length == 0:
        return 0
    probabilities = [float(h) / histogram_length for h in histogram if h != 0]
    return -sum(p * math.log2(p) for p in probabilities)

def build_svg_with_webp_embed(width: int, height: int, webp_b64: str) -> str:
    data_uri = f"data:image/webp;base64,{webp_b64}"
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">\n'
        f'  <image width="{width}" height="{height}" href="{data_uri}"/>\n'
        "</svg>\n"
    )

def process_images(raw_paths: list[str]) -> None:
    global total_files, successful_conversions, total_original_kb, total_output_kb
    use_downloads = not batch_includes_folder(raw_paths)
    file_paths = collect_image_paths(raw_paths)
    if not file_paths:
        status_label.config(text="No supported images found.")
        logger.info("No supported images in selection.")
        return

    total_files = len(file_paths)
    successful_conversions = 0
    total_original_kb = 0.0
    total_output_kb = 0.0

    # Initialize status label
    mode_hint = "Downloads" if use_downloads else "In-place (originals removed after OK)"
    status_label.config(text=f"Preparing…\n({mode_hint})")
    root.update_idletasks()

    for i, file_path in enumerate(file_paths, 1):
        file_ext = os.path.splitext(file_path)[1].lower()

        try:
            # Open image and get original size
            original_size_kb = os.path.getsize(file_path) / 1024
            img = Image.open(file_path)

            # Optimize PNG inputs in memory
            if file_ext == ".png":
                buf = io.BytesIO()
                img.save(buf, format="PNG", optimize=True)
                buf.seek(0)
                img = Image.open(buf)

            # Convert to RGB if necessary
            if img.mode in ("RGBA", "LA"):
                img = img.convert("RGB")

            # Resize to max 1000px
            max_dimensions = (1000, 1000)
            img.thumbnail(max_dimensions, Image.Resampling.LANCZOS)

            w, h = img.size

            # Determine compression settings based on entropy
            entropy = calculate_entropy(img)
            if entropy < 4.0:  # Low complexity (e.g., text, logos)
                quality = 60
                lossless = True
            else:  # High complexity (e.g., photos)
                quality = 75
                lossless = False

            save_params = {
                "format": "WEBP",
                "quality": quality if not lossless else 100,
                "lossless": lossless,
                "method": 6,  # Maximum compression effort
                "exif": b"",  # Strip EXIF metadata
                "icc_profile": None  # Strip ICC profile
            }
            webp_buf = io.BytesIO()
            img.save(webp_buf, **save_params)
            webp_bytes = webp_buf.getvalue()
            webp_b64 = base64.b64encode(webp_bytes).decode("ascii")

            svg_body = build_svg_with_webp_embed(w, h, webp_b64)
            output_filename = os.path.splitext(os.path.basename(file_path))[0] + ".svg"
            if use_downloads:
                output_path = os.path.join(output_folder, output_filename)
            else:
                output_path = os.path.join(os.path.dirname(file_path), output_filename)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(svg_body)

            output_size_kb = os.path.getsize(output_path) / 1024
            total_original_kb += original_size_kb
            total_output_kb += output_size_kb

            logger.info(
                f"Successfully converted {file_path} to {output_path} "
                f"(quality={quality}, lossless={lossless}, webp_embed={len(webp_bytes) / 1024:.1f}KB, "
                f"original={original_size_kb:.1f}KB, output_svg={output_size_kb:.1f}KB)")
            successful_conversions += 1

            if not use_downloads:
                try:
                    os.remove(file_path)
                    logger.info(f"Removed original after successful convert: {file_path}")
                except OSError as exc:
                    logger.error(f"Converted but could not remove original {file_path}: {exc}")

        except Exception as e:
            logger.error(f"Failed to convert {file_path}: {str(e)}")

        # Update status label with counter
        status_label.config(text=f"Processing:\n{i}/{total_files} {'image' if total_files == 1 else 'images'}")
        root.update_idletasks()
        time.sleep(0.01)  # Slight delay for visible updates

    # Show final status
    where = f"→ {output_folder}" if use_downloads else "(in-place)"
    status_text = (
        f"Success: {successful_conversions}/{total_files} {where}\n"
        f"Original: {total_original_kb:.1f} KB → Output: {total_output_kb:.1f} KB"
    )
    status_label.config(text=status_text)
    logger.info(status_text)

def select_files():
    files = filedialog.askopenfilenames(
        title="Select Images",
        filetypes=[("Image files", "*.png *.jpg *.jpeg *.webp")]
    )
    if files:
        process_images(list(files))


def select_folder():
    folder, _source = pick_root_folder()
    if not folder:
        return
    folder = resolve_directory_root(normalize_dnd_path(folder))
    process_images([folder])


def drop(event):
    file_paths = list(root.tk.splitlist(event.data))
    process_images(file_paths)

# UI Elements
frame = tk.Frame(root, bg="#2B2B2B")
frame.pack(pady=20)

instruction_label = tk.Label(
    frame,
    text=(
        "drop image files only → svg in Downloads/Converted_Images\n"
        "drop a folder (or Select folder) → svg in place; "
        "original removed if OK (failed files kept)\n"
        "png, jpg, webp (WebP inside svg)"
    ),
    bg="#2B2B2B", fg="#FFFFFF", font=("Arial", 10),
    justify=tk.CENTER,
)
instruction_label.pack(pady=10)

btn_row = tk.Frame(frame, bg="#2B2B2B")
btn_row.pack(pady=5)
select_button = tk.Button(btn_row, text="Select images", command=select_files,
                          bg="#3C3F41", fg="#FFFFFF", font=("Arial", 10), activebackground="#4B4B4B")
select_button.pack(side=tk.LEFT, padx=4)
folder_button = tk.Button(btn_row, text="Select folder", command=select_folder,
                          bg="#3C3F41", fg="#FFFFFF", font=("Arial", 10), activebackground="#4B4B4B")
folder_button.pack(side=tk.LEFT, padx=4)

status_label = tk.Label(frame, text="", bg="#2B2B2B", fg="#FFFFFF", font=("Arial", 10))
status_label.pack(pady=10)

# Enable drag-and-drop
root.drop_target_register(tkdnd.DND_FILES)
root.dnd_bind('<<Drop>>', drop)

# Start the application
root.mainloop()
