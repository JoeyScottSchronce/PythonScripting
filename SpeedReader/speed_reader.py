"""Import all packages"""

import tkinter as tk
from tkinter import filedialog
import threading
import re  # Regular expression module for splitting text into words
import fitz  # PyMuPDF, for reading PDF files
import docx  # python-docx, for reading DOCX files

class ReadingAssistant:
    """The entire reading assistant app in one class"""
    def __init__(self, master):
        # Initialize the main window
        self.master = master
        self.master.title("Speed Reading Assistant")

        # Set background color of the main window
        self.master.configure(bg='black')

        # Center the window on the screen
        window_width = 1400
        window_height = 400
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        center_x = int(screen_width/2 - window_width / 2)
        center_y = int(screen_height/2 - window_height / 2)
        self.master.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")

        # Top frame for completed label and upload button
        self.top_frame = tk.Frame(master, bg='black')
        self.top_frame.pack(fill=tk.X, padx=20, pady=20)

        # Percentage completed label, in the upper left side
        self.total_char_count = 0
        self.percentage_completed_label = tk.Label(self.top_frame, text="Completed:   0 %",
                                                  fg="white", font=("Arial", 12), bg='black')
        self.percentage_completed_label.pack(side=tk.LEFT)

        # Button to upload a document, in the upper right side
        self.load_text_button = tk.Button(self.top_frame, bg="lightgrey",
                                          text="Upload Document", command=self.load_text)
        self.load_text_button.pack(side=tk.RIGHT, padx=(10, 10))

        # Button to load text from clipboard, next to the upload document button
        self.load_clipboard_button = tk.Button(self.top_frame, bg="lightgrey", text="Clipboard",
                                               command=self.load_clipboard)
        self.load_clipboard_button.pack(side=tk.RIGHT, padx=(0, 0))

        # Display label for showing words, centered
        self.label = tk.Label(master, text="", fg="white",
                              font=("Arial", 40), bg='black', width=50, height=2)
        self.label.config(text="Upload to Begin")
        self.label.pack(expand=True, padx=10, pady=10)

        # Initialize variables for word display logic
        self.text = ""  # Full text to display
        self.running = False  # Flag to control reading state
        self.current_char_index = 0  # Index of the current character position
        self.word_delay = 0.04  # Delay between character shifts, adjustable by user
        self.display_width = 50  # Number of characters to display (matches label width)

        # Calculate words per minute (approximate, based on average word length)
        self.words_per_minute = int(60 / self.word_delay / 5)  # Assume 5 chars per word

        # Binding buttons events to start and stop reading
        self.master.bind("<Right>", self.start_reading)
        self.master.bind("<KeyRelease-Right>", self.stop_reading)
        self.master.bind("<Return>", self.start_reading)
        self.master.bind("<Shift_R>", self.stop_reading)
        self.master.bind("<ButtonPress-3>", self.start_reading)
        self.master.bind("<ButtonRelease-3>", self.stop_reading)

        # Bottom frame for words per minute controls and rewind button
        self.bottom_frame = tk.Frame(master, bg='black')
        self.bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=20)

        # Frame for words per minute controls to keep them on the left side
        self.wpm_frame = tk.Frame(self.bottom_frame, bg='black')
        self.wpm_frame.pack(side=tk.LEFT, padx=(20, 10))

        # Buttons to adjust the words per minute, within the wpm frame
        self.increase_wpm_button = tk.Button(self.wpm_frame, text="Faster",
                                            bg="lightgrey", command=self.increase_wpm)
        self.increase_wpm_button.pack(side=tk.LEFT, padx=(0, 10))
        self.decrease_wpm_button = tk.Button(self.wpm_frame, text="Slower",
                                            bg="lightgrey", command=self.decrease_wpm)
        self.decrease_wpm_button.pack(side=tk.LEFT, padx=(0, 0))

        # Label to display the current words per minute
        self.wpm_value_label = tk.Label(self.wpm_frame, fg="white",
                                        text=f"Words per minute: {self.words_per_minute}",
                                        font=("Arial", 12), bg='black')
        self.wpm_value_label.pack(side=tk.LEFT, padx=(10, 10))

        # Rewind button on the right side of the bottom frame
        self.rewind_button = tk.Button(self.bottom_frame, text="Go Back",
                                       bg="lightgrey", command=self.rewind_one_word)
        self.master.bind("<Left>", lambda event: self.rewind_one_word())
        self.rewind_button.pack(side=tk.RIGHT, padx=(10, 20))

    def clean_words(self, text):
        """Cleans text by normalizing spaces and adding padding"""
        # Normalize spaces and add padding spaces
        cleaned_text = ' '.join(text.split())
        # Add enough spaces at start and end to make label appear empty
        padding = " " * self.display_width
        return padding + cleaned_text + padding

    def load_text(self):
        """Imports any file or documents to be read"""
        file_path = filedialog.askopenfilename()
        if file_path:
            # Load the document based on its file extension
            if file_path.endswith('.pdf'):
                text = self.read_pdf(file_path)
            elif file_path.endswith('.docx'):
                text = self.read_docx(file_path)
            else:  # Treat as a plain text file
                with open(file_path, "r", encoding="utf-8", errors='ignore') as file:
                    text = file.read()
            self.text = self.clean_words(text)
            # Update the total character count
            self.total_char_count = len(self.text)
            self.update_percentage_completed(0)
            if self.text.strip():  # Check if text has non-space characters
                self.label.config(text="Press Enter to start")
                self.current_char_index = 0
            else:
                self.label.config(text="File is Blank!")

    def load_clipboard(self):
        """Imports material to be read from the clipboard"""
        try:
            clipboard_text = self.master.clipboard_get()
            if clipboard_text:
                self.text = self.clean_words(clipboard_text)
                self.total_char_count = len(self.text)
                self.update_percentage_completed(0)
                if self.text.strip():  # Check if text has non-space characters
                    self.label.config(text="Press Enter to start")
                    self.current_char_index = 0
                else:
                    self.label.config(text="Clipboard is Empty..")
            else:
                self.label.config(text="Clipboard is Empty...")
        except tk.TclError:
            self.label.config(text="Clipboard is Empty!")

    def read_docx(self, file_path):
        """Read DOCX file and return text"""
        text = ""
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            text += para.text + " "
        return text

    def read_pdf(self, file_path):
        """Read PDF file and return text"""
        text = ""
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text()
        return text

    def increase_wpm(self):
        """Function to increase words per minute to read faster"""
        self.words_per_minute += 10
        self.word_delay = 60 / (self.words_per_minute * 5)  # Adjust for chars
        self.wpm_value_label.config(text=f"Words per minute: {self.words_per_minute}")

    def decrease_wpm(self):
        """Function to decrease words per minute to read slower"""
        self.words_per_minute -= 10
        if self.words_per_minute < 10:
            self.words_per_minute = 10
        self.word_delay = 60 / (self.words_per_minute * 5)  # Adjust for chars
        self.wpm_value_label.config(text=f"Words per minute: {self.words_per_minute}")

    def display_words(self):
        """Function to display text in the GUI with a carousel effect"""
        if self.running and self.current_char_index <= len(self.text):
            # Get the substring to display
            start = max(0, self.current_char_index - self.display_width // 2)
            end = min(len(self.text), start + self.display_width)
            display_text = self.text[start:end]
            # Pad with spaces if needed to maintain width
            if len(display_text) < self.display_width:
                display_text += " " * (self.display_width - len(display_text))
            self.label.config(text=display_text)
            self.current_char_index += 1
            # Schedule the next update
            self.master.after(int(self.word_delay * 1000), self.display_words)
        else:
            self.running = False

        # Update percentage completed
        if self.total_char_count > 0:
            percentage_completed = (self.current_char_index / self.total_char_count) * 100
            self.update_percentage_completed(percentage_completed)

    def update_percentage_completed(self, percentage):
        """Function to update the 'Completed' label on the GUI"""
        rounded_percentage = round(percentage)
        self.percentage_completed_label.config(text=f"Completed: {rounded_percentage} %")

    def start_reading(self, event=None):
        """Function to start the carousel display"""
        if not self.running:
            self.running = True
            if self.current_char_index <= len(self.text):
                threading.Thread(target=self.display_words).start()
            else:
                self.current_char_index = 0

    def stop_reading(self, event):
        """Function to stop the carousel display"""
        self.running = False

    def rewind_one_word(self):
        """Function to go back by one word in the text"""
        if self.current_char_index > self.display_width:  # Ensure we don't rewind past initial padding
            # Find the previous word boundary (space)
            temp_index = self.current_char_index - 2
            while temp_index > self.display_width and self.text[temp_index] != " ":
                temp_index -= 1
            self.current_char_index = temp_index + 1
            # Update display immediately
            start = max(0, self.current_char_index - self.display_width // 2)
            end = min(len(self.text), start + self.display_width)
            display_text = self.text[start:end]
            if len(display_text) < self.display_width:
                display_text += " " * (self.display_width - len(display_text))
            self.label.config(text=display_text)

def main():
    """Main function of the app"""
    root = tk.Tk()
    ReadingAssistant(root)
    root.mainloop()

if __name__ == "__main__":
    main()