"""
Flashcard Builder - AI-powered flashcard generation for Anki
Generates flashcards from Gemini API and creates Anki decks
"""
import tkinter as tk
from tkinter import messagebox
import requests
import json
import genanki
import random
from pathlib import Path
import os
from dotenv import load_dotenv
import threading

# Load environment variables from .env file
load_dotenv()

# ============ CONFIGURATION CONSTANTS ============
# Colors
COLOR_BG_PRIMARY = '#2E2E2E'
COLOR_BG_SECONDARY = '#4A4A4A'
COLOR_TEXT_PRIMARY = '#E0E0E0'
COLOR_TEXT_SECONDARY = 'white'

# Window settings
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 500
CANVAS_WIDTH = 880
CANVAS_HEIGHT = 480

# Fonts
FONT_TITLE = ("Arial", 14)
FONT_LARGE = ("Arial", 12)
FONT_STANDARD = ("Arial", 16)
FONT_LOADING = ("Arial", 68)

# API Settings
GEMINI_API_MODEL = "gemini-2.5-flash"
RESPONSE_MIME_TYPE = "application/json"

# UI Padding/Spacing
PADDING_STANDARD = 10
PADDING_LARGE = 20

# Entry field widths
ENTRY_WIDTH_QUESTION = 85
ENTRY_WIDTH_ANSWER = 30

# ============ CORE FUNCTIONS ============

# Anki deck creation
def create_anki_deck(title, flashcards):
    """
    Create an Anki deck from a list of flashcards and save to Downloads folder.
    
    Args:
        title (str): The name of the deck
        flashcards (list): List of dicts with 'question' and 'answer' keys
    
    Returns:
        str: Path to the created .apkg file
    """
    if not flashcards:
        raise ValueError("Cannot create deck with no flashcards")
    
    model_id = random.randrange(1 << 30, 1 << 31)
    model = genanki.Model(
        model_id,
        title,
        fields=[
            {'name': 'Front'},
            {'name': 'Back'}
        ],
        templates=[
            {
                'name': 'Card 1',
                'qfmt': '{{Front}}',
                'afmt': '{{FrontSide}}<hr id=answer>{{Back}}',
            }
        ],
        css='.card {font-family: Arial; font-size: 20px; text-align: center; color: black; background-color: white;}'
    )
    
    deck_id = random.randrange(1 << 30, 1 << 31)
    deck = genanki.Deck(deck_id, title)
    
    for card in flashcards:
        note = genanki.Note(
            model=model,
            fields=[card['question'], card['answer']]
        )
        deck.add_note(note)
    
    output_path = os.path.join(Path.home(), 'Downloads', f'{title}.apkg')
    genanki.Package(deck).write_to_file(output_path)
    return output_path


def validate_flashcard(card):
    """
    Validate that a flashcard has required keys and non-empty values.
    
    Args:
        card (dict): Flashcard to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    if not isinstance(card, dict):
        return False
    
    question = card.get('question', '').strip()
    answer = card.get('answer', '').strip()
    
    return bool(question and answer)


def parse_response_text(text):
    """
    Parse API response text into a list of flashcards.
    Handles both JSON array and object with 'flashcards' key.
    Validates each flashcard for required fields.
    
    Args:
        text (str): JSON response from API
    
    Returns:
        list: List of validated flashcard dictionaries
    """
    flashcards = []
    
    if not text or not text.strip():
        return flashcards
    
    try:
        data = json.loads(text)
        
        # Extract flashcards based on data structure
        cards = []
        if isinstance(data, list):
            cards = data
        elif isinstance(data, dict) and 'flashcards' in data:
            cards = data['flashcards']
        else:
            return flashcards
        
        # Validate and filter flashcards
        for card in cards:
            if validate_flashcard(card):
                flashcards.append({
                    'question': card.get('question', '').strip(),
                    'answer': card.get('answer', '').strip()
                })
    
    except json.JSONDecodeError:
        # Silent fail - return empty list on invalid JSON
        pass
    
    return flashcards

# Main Application
class FlashcardApp:
    """AI-powered Flashcard Application for generating and managing Anki decks."""
    
    # API prompt template
    API_SYSTEM_PROMPT = (
        "ROLE: You are a flashcard generator. All flashcard content should be "
        "generated based on current and official information. "
        "\n\n"
        "RESPONSE FORMAT: Return a valid JSON array of objects with 'question' and 'answer' keys. "
        "Example: [{\"question\": \"Where is Rome?\", \"answer\": \"Italy\"}, "
        "{\"question\": \"What is 2+2?\", \"answer\": \"4\"}]\n\n"
        "REQUIREMENTS:\n"
        "- Always format response as valid JSON only (no additional text)\n"
        "- Use simple, clear language\n"
        "- Cover the topic comprehensively\n"
        "- Generate as many flashcards as possible\n"
        "- Questions should be phrased as if asking someone\n"
        "- Answers must be extremely brief and memorable\n"
        "- For programming topics, use Golang as the preferred language\n"
        "- Do not include HTML in the response\n"
    )
    
    def __init__(self, root):
        """
        Initialize the Flashcard Application.
        
        Args:
            root (tk.Tk): The root window
        """
        self.root = root
        self.root.title("Flashcard Creator")
        self.flashcards = []
        self.check_vars = []
        self.loading_label = None
        self.loading_animation = None
        self.loading_index = 0
        
        # Set fixed window size and dark background
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.resizable(False, False)
        self.root.configure(bg=COLOR_BG_PRIMARY)
        
        # Initialize main UI
        self.show_main_frame()

    def show_main_frame(self):
        """Display the main input frame for entering flashcard topics."""
        # Destroy existing frame if any
        if hasattr(self, 'main_frame'):
            self.main_frame.destroy()

        # Create main frame
        self.main_frame = tk.Frame(self.root, bg=COLOR_BG_PRIMARY)
        self.main_frame.pack(expand=True, fill='both')

        # Create inner frame to hold widgets
        inner_frame = tk.Frame(self.main_frame, bg=COLOR_BG_PRIMARY)
        inner_frame.pack(expand=True, anchor="center")

        # Label with centered text
        tk.Label(
            inner_frame,
            text="Generate a list of flashcards about...",
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_BG_PRIMARY,
            font=FONT_LARGE,
            width=60,
            anchor="center"
        ).pack(pady=PADDING_STANDARD)

        # Entry with centered text
        self.text_input = tk.Entry(
            inner_frame,
            width=30,
            bg=COLOR_BG_SECONDARY,
            fg=COLOR_TEXT_SECONDARY,
            insertbackground=COLOR_TEXT_SECONDARY,
            font=FONT_STANDARD,
            justify="center"
        )
        self.text_input.pack(pady=PADDING_STANDARD)

        # Submit button
        tk.Button(
            inner_frame,
            text="Generate",
            command=self.submit_to_api,
            font=FONT_LARGE,
            bg=COLOR_BG_SECONDARY,
            fg=COLOR_TEXT_SECONDARY,
            width=10,
            justify="center"
        ).pack(pady=PADDING_STANDARD)

        # Bind Enter key to submit_to_api
        self.root.bind('<Return>', lambda event: self.submit_to_api())

    def show_loading(self):
        """Display loading animation."""
        # Clear main frame content
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # Show loading label
        self.loading_label = tk.Label(
            self.main_frame,
            text=".",
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_BG_PRIMARY,
            font=FONT_LOADING
        )
        self.loading_label.pack(expand=True)
        self.update_loading()

    def update_loading(self):
        """Update loading animation with increasing dots."""
        if self.loading_label:
            dots = '.' * (self.loading_index % 3 + 1)
            self.loading_label.config(text=dots)
            self.loading_index += 1
            self.loading_animation = self.root.after(1000, self.update_loading)

    def hide_loading(self):
        """Stop animation and remove loading label."""
        if self.loading_animation:
            self.root.after_cancel(self.loading_animation)
            self.loading_animation = None
        if self.loading_label:
            self.loading_label.destroy()
            self.loading_label = None
        self.loading_index = 0

    def run_api_request(self, input_text):
        """
        Run API request in a separate thread.
        
        Args:
            input_text (str): The topic to generate flashcards for
        """
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                self.root.after(0, self.handle_api_error, 
                              "Gemini API key not found in .env file.")
                return

            url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_API_MODEL}:generateContent"
            headers = {"Content-Type": "application/json"}
            data = {
                "contents": [{
                    "parts": [{
                        "text": self.API_SYSTEM_PROMPT + 
                               f"REQUEST: Generate a verbose and comprehensive list of "
                               f"flashcards about {input_text}?"
                    }]
                }],
                "generationConfig": {
                    "response_mime_type": RESPONSE_MIME_TYPE
                }
            }

            response = requests.post(f"{url}?key={api_key}", headers=headers, json=data)
            response.raise_for_status()

            # Parse response
            response_data = response.json()
            response_text = (response_data
                           .get("candidates", [{}])[0]
                           .get("content", {})
                           .get("parts", [{}])[0]
                           .get("text", ""))
            
            if not response_text:
                self.root.after(0, self.handle_api_error, "No valid response from API.")
                return

            # Process response in main thread
            self.root.after(0, self.process_input, response_text)

        except requests.exceptions.RequestException as e:
            self.root.after(0, self.handle_api_error, f"API request failed: {str(e)}")
        except json.JSONDecodeError:
            self.root.after(0, self.handle_api_error, "Invalid response format from API.")
        except Exception as e:
            self.root.after(0, self.handle_api_error, f"Unexpected error: {str(e)}")

    def handle_api_error(self, error_message):
        """
        Handle API errors by showing error dialog and returning to main frame.
        
        Args:
            error_message (str): The error message to display
        """
        self.hide_loading()
        self.show_main_frame()
        messagebox.showerror("Error", error_message)

    def submit_to_api(self):
        """Submit input text to API for flashcard generation."""
        input_text = self.text_input.get().strip()
        if not input_text:
            messagebox.showwarning("Warning", "Please enter some text to process!")
            return

        self.show_loading()
        threading.Thread(target=self.run_api_request, args=(input_text,), daemon=True).start()

    def process_input(self, text):
        """
        Process API response and display review page.
        
        Args:
            text (str): The JSON response from API
        """
        self.flashcards = parse_response_text(text)
        self.hide_loading()
        
        if not self.flashcards:
            self.show_main_frame()
            messagebox.showwarning("Warning", 
                                 "No valid flashcards found in API response!")
            return
        
        self.show_review_page()

    def show_review_page(self):
        """Display review page where user can edit and select flashcards."""
        # Destroy existing frame
        if hasattr(self, 'main_frame'):
            self.main_frame.destroy()

        # Create main frame for review page
        self.main_frame = tk.Frame(self.root, bg=COLOR_BG_PRIMARY)
        self.main_frame.pack(expand=True, fill='both')

        # Create canvas and scrollbar for review page
        self.canvas = tk.Canvas(
            self.main_frame,
            width=CANVAS_WIDTH,
            height=CANVAS_HEIGHT,
            bg=COLOR_BG_PRIMARY,
            highlightthickness=0
        )
        self.scrollbar = tk.Scrollbar(self.main_frame, orient="vertical",
                                     command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        # Create scrollable frame
        self.scroll_frame = tk.Frame(self.canvas, bg=COLOR_BG_PRIMARY)
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.scroll_frame,
                                                     anchor="nw")

        # Update scroll region when frame size changes
        self.scroll_frame.bind("<Configure>",
                              lambda e: self.canvas.configure(
                                  scrollregion=self.canvas.bbox("all")))

        # Bind mouse wheel to scroll
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # Create centered content frame
        content_frame = tk.Frame(self.scroll_frame, bg=COLOR_BG_PRIMARY)
        content_frame.pack(expand=True, fill='x', pady=PADDING_STANDARD)

        # Review page title
        tk.Label(content_frame,
                text="Review New Flashcards",
                font=FONT_TITLE,
                fg=COLOR_TEXT_PRIMARY,
                bg=COLOR_BG_PRIMARY).pack(pady=PADDING_STANDARD, anchor='center')

        self.check_vars = []
        self.question_entries = []
        self.answer_entries = []

        # Create flashcard entries
        for i, card in enumerate(self.flashcards):
            self._create_flashcard_row(content_frame, card, i)

        # Deck title section
        tk.Label(content_frame,
                text="Deck Title:",
                fg=COLOR_TEXT_PRIMARY,
                bg=COLOR_BG_PRIMARY).pack(pady=PADDING_STANDARD, anchor='center')
        
        self.title_entry = tk.Entry(
            content_frame,
            bg=COLOR_BG_SECONDARY,
            fg=COLOR_TEXT_SECONDARY,
            insertbackground=COLOR_TEXT_SECONDARY,
            justify="center"
        )
        self.title_entry.pack(pady=PADDING_STANDARD, anchor='center')

        # Button frame
        button_frame = tk.Frame(content_frame, bg=COLOR_BG_PRIMARY)
        button_frame.pack(pady=PADDING_STANDARD, anchor='center')

        tk.Button(button_frame,
                 text="Create New Deck",
                 command=self.create_deck,
                 bg=COLOR_BG_SECONDARY,
                 fg=COLOR_TEXT_SECONDARY).pack(side='left', padx=PADDING_STANDARD)

        tk.Button(button_frame,
                 text="Back",
                 command=self.return_to_main,
                 bg=COLOR_BG_SECONDARY,
                 fg=COLOR_TEXT_SECONDARY).pack(side='left', padx=PADDING_STANDARD)

    def _create_flashcard_row(self, parent, card, index):
        """
        Create a single flashcard edit row.
        
        Args:
            parent (tk.Frame): Parent frame
            card (dict): Flashcard data
            index (int): Row index
        """
        row_frame = tk.Frame(parent, bg=COLOR_BG_PRIMARY)
        row_frame.pack(pady=2, anchor='center')

        # Checkbox
        var = tk.BooleanVar(value=True)
        self.check_vars.append(var)
        tk.Checkbutton(row_frame,
                      variable=var,
                      bg=COLOR_BG_PRIMARY,
                      fg=COLOR_TEXT_SECONDARY,
                      selectcolor=COLOR_BG_SECONDARY).pack(side='left',
                                                           padx=PADDING_STANDARD)

        # Question field
        tk.Label(row_frame,
                text="Q:",
                fg=COLOR_TEXT_PRIMARY,
                bg=COLOR_BG_PRIMARY).pack(side='left', padx=PADDING_STANDARD)
        
        q_entry = tk.Entry(row_frame,
                          width=ENTRY_WIDTH_QUESTION,
                          bg=COLOR_BG_SECONDARY,
                          fg=COLOR_TEXT_SECONDARY,
                          insertbackground=COLOR_TEXT_SECONDARY)
        q_entry.insert(0, card['question'])
        q_entry.pack(side='left', padx=PADDING_STANDARD)
        self.question_entries.append(q_entry)

        # Answer field
        tk.Label(row_frame,
                text="A:",
                fg=COLOR_TEXT_PRIMARY,
                bg=COLOR_BG_PRIMARY).pack(side='left', padx=PADDING_STANDARD)
        
        a_entry = tk.Entry(row_frame,
                          width=ENTRY_WIDTH_ANSWER,
                          bg=COLOR_BG_SECONDARY,
                          fg=COLOR_TEXT_SECONDARY,
                          insertbackground=COLOR_TEXT_SECONDARY)
        a_entry.insert(0, card['answer'])
        a_entry.pack(side='left', padx=PADDING_STANDARD)
        self.answer_entries.append(a_entry)

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling."""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def create_deck(self):
        """Create Anki deck from selected flashcards and show success message."""
        title = self.title_entry.get().strip() or "Untitled Deck"
        
        selected_flashcards = [
            {
                'question': self.question_entries[i].get().strip(),
                'answer': self.answer_entries[i].get().strip()
            }
            for i in range(len(self.flashcards))
            if self.check_vars[i].get()
        ]
        
        # Filter out empty entries
        selected_flashcards = [card for card in selected_flashcards
                              if card['question'] and card['answer']]
        
        if not selected_flashcards:
            messagebox.showwarning("Warning", "No valid flashcards selected!")
            return

        try:
            output_path = create_anki_deck(title, selected_flashcards)
            self._show_success_page()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create deck: {str(e)}")

    def _show_success_page(self):
        """Display success message after deck creation."""
        # Clear old widgets
        if hasattr(self, 'canvas'):
            self.canvas.destroy()
        if hasattr(self, 'scrollbar'):
            self.scrollbar.destroy()
        if hasattr(self, 'main_frame'):
            self.main_frame.destroy()

        # Create new main frame for success page
        self.main_frame = tk.Frame(self.root, bg=COLOR_BG_PRIMARY)
        self.main_frame.pack(expand=True, fill='both')

        tk.Label(self.main_frame,
                text="Flashcard deck created in Downloads folder!",
                font=FONT_TITLE,
                fg=COLOR_TEXT_PRIMARY,
                bg=COLOR_BG_PRIMARY).pack(pady=PADDING_LARGE, anchor='center')
        
        tk.Button(self.main_frame,
                 text="Return to Home",
                 command=self.return_to_main,
                 bg=COLOR_BG_SECONDARY,
                 fg=COLOR_TEXT_SECONDARY).pack(pady=PADDING_STANDARD, anchor='center')

    def return_to_main(self):
        """Return to the main input frame."""
        self.show_main_frame()


if __name__ == "__main__":
    root = tk.Tk()
    app = FlashcardApp(root)
    root.mainloop()