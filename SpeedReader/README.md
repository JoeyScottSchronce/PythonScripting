## Speed Reading Assistant
A simple speed reading application I built with Python and Tkinter when I first began learning python.
This software is a desktop program designed to help improve your reading speed by displaying text one word at a time.

## Features
- Import text from PDF, DOCX, or plain text files
- Load text directly from the clipboard
- Adjustable reading speed (words per minute)
- Percentage completed indicator
- Rewind function to go back words
- Simple and intuitive GUI

## Requirements
- Python 3.12
- PyMuPDF (`fitz`)
- python-docx (`docx`)
- Tkinter (usually included with Python installations)
- re (standard library, included with Python)
- threading (standard library, included with Python)

## Installation
1. **Fork the repository:**<br>
**Remove the other scripts from the repository, then cd into the SpeedReader directory.**

```
cd SpeedReader
```
2. **Install the required packages:**<br>
**Open a terminal and run the following command (all packages have to be in the environment you plan to run the Speed Reader script)**
```
pip install pymupdf python-docx pyinstaller
```

3. **Make any changes you wish to personalize the UI or functionality in an IDE, then continue on to Usage.**

## Usage
1. **Save the file as a `.py` file with pyinstaller.**

2. **Create a shortcut on your desktop to run the software. Your "Target" will resemble this filepath:** <br>
   ```"C:\Program Files\Python312\pythonw.exe" "C:\Users\<Username>\<path to saved file>\speed_reader.py"``` <br>
   **This will create a standalone executable without a console window. Change the icon and other details to suit your needs.**
   
3. **Run the application with the new shortcut**


## **How to use the GUI:**
- Click "Upload Document" to import a PDF, DOCX, or plain text file.
- Click "Clipboard" to load the last copied text directly from the clipboard.
- Press Enter to start auto-reader and right click mouse to stop auto-reader.
- Press left arrow to go back one word or hold to rewind to the beginning.
- press right arrow to go forward one word or hold to read manually.
- Adjust the reading speed using the "Faster" and "Slower" buttons.
- Use the "Go Back" button or press right arrow to rewind by one word.

## Acknowledgments
- [Python](https://www.python.org/)
- [Tkinter](https://docs.python.org/3/library/tkinter.html)
- [PyMuPDF](https://pymupdf.readthedocs.io/en/latest/)
- [python-docx](https://python-docx.readthedocs.io/en/latest/)
