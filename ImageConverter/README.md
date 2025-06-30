## Image Converter
A Python application built with Tkinter and TkinterDnD2 that converts PNG and JPG images to WebP format with adaptive compression, featuring drag-and-drop support and detailed logging.


## Features
- Convert PNG and JPG images to WebP with optimized compression
- Drag-and-drop images for easy batch processing
- Adaptive compression based on image complexity (entropy calculation)
- Resize images to a maximum of 1000px dimensions
- Log conversion details (success, skips, size savings) to a file
- Dark-themed, compact GUI with real-time status updates

## Requirements
- Python 3.7+
- tkinter (included with Python)
- Pillow (PIL)
- tkinterdnd2
- logging (standard library, included with Python)
- pathlib (standard library, included with Python)
- math (standard library, included with Python)
- time (standard library, included with Python)

## Installation
1. Fork this repository on GitHub to create your own copy for customization or contribution.

2. Install the required packages: <br>
Open a terminal and run:
```
pip install Pillow tkinterdnd2 pyinstaller
```

3. Make any changes you wish to personalize the UI or functionality in an IDE, then continue to Usage.

## Usage
1. Save the file as a .py file with pyinstaller.  
```
pyinstaller --onefile image_converter.py
```

2. Create a shortcut on your desktop to run the software. Your "Target" will resemble this filepath:  
```
C:\Program Files\Python37\pythonw.exe "C:\Users\<Username>\<path to saved file>\dist\image_converter.exe"
```
This will create a standalone executable without a console window. Change the icon and other details to suit your needs.

3. Run the application with the new shortcut.


## How to use the GUI:
- Drag and drop PNG or JPG images onto the window to convert them to WebP.
- Alternatively, click "Select Images" to browse and select image files.
- Watch the status label for real-time updates on conversion progress.
- Converted images are saved in the Converted_Images folder in your Downloads directory.
- Check the log.txt file in the Converted_Images folder for detailed conversion stats, including size savings and skipped files.

## Notes
- Only PNG and JPG files are supported; WebP files are skipped.
- Images are resized to a maximum of 1000px for efficiency.
- Compression settings (quality and lossless mode) are automatically adjusted based on image complexity.
- Conversion logs are saved to Converted_Images/log.txt in the Downloads folder.

## Acknowledgments
- Python
- Tkinter
- Pillow
- TkinterDnD2

