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

# Anki deck creation
def create_anki_deck(title, flashcards):
    model_id = random.randrange(1 << 30, 1 << 31)
    model = genanki.Model(
        model_id,
        f'{title}',
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
        css='''.card {font-family: ariel;font-size: 20px;text-align: center;color: black;background-color:white;}'''

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

# Parse response text into flashcards (CSV format: question|answer;question|answer;...)
def parse_response_text(text):
    flashcards = []
    pairs = text.strip().split(';;;')
    for pair in pairs:
        if '|||' in pair:
            question, answer = pair.split('|||', 1)
            flashcards.append({"question": question.strip(), "answer": answer.strip()})
    return flashcards

# Main Application
class FlashcardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Flashcard Creator")
        self.flashcards = []
        self.check_vars = []
        self.loading_label = None
        self.loading_animation = None
        self.loading_index = 0

        # Set fixed window size and dark background
        self.root.geometry("900x500")
        self.root.resizable(False, False)
        self.root.configure(bg='#2E2E2E')

        # Initialize main UI
        self.show_main_frame()

    def show_main_frame(self):
        # Destroy existing frame if any
        if hasattr(self, 'main_frame'):
            self.main_frame.destroy()

        # Create main frame
        self.main_frame = tk.Frame(self.root, bg='#2E2E2E')
        self.main_frame.pack(expand=True, fill='both')

        # Create inner frame to hold widgets
        inner_frame = tk.Frame(self.main_frame, bg='#2E2E2E')
        inner_frame.pack(expand=True, anchor="center")

        # Label with centered text
        tk.Label(
            inner_frame,  # Use local inner_frame, not self.inner_frame
            text="Generate a list of flashcards about...",
            fg='#E0E0E0',
            bg='#2E2E2E',
            font=("Arial", 12),
            width=60,  # Match Entry width for visual alignment
            anchor="center"  # Centers text within the label's width
        ).pack(pady=10)

        # Entry with centered text
        self.text_input = tk.Entry(
            inner_frame,  # Use local inner_frame
            width=30,
            bg='#4A4A4A',
            fg='white',
            insertbackground='white',
            font=("Arial", 16),
            justify="center"  # Centers text inside the entry
        )
        self.text_input.pack(pady=10)

        # Submit button with centered text
        tk.Button(
            inner_frame,  # Use local inner_frame
            text="Generate",
            command=self.submit_to_api,
            font=("Arial", 12),
            bg='#4A4A4A',
            fg='white',
            width=10,  # Smaller width for button, still centered
            justify="center"  # Ensures the text is centered (default for single-line)
        ).pack(pady=10)

        # Bind Enter key to submit_to_api
        self.root.bind('<Return>', lambda event: self.submit_to_api())

    def show_loading(self):
        # Clear main frame content
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # Show loading label
        self.loading_label = tk.Label(self.main_frame, text=".",
                                     fg='#E0E0E0', bg='#2E2E2E', font=("Arial", 68))
        self.loading_label.pack(expand=True)
        self.update_loading()

    def update_loading(self):
        # Update loading animation with increasing dots
        if self.loading_label:
            dots = '.' * (self.loading_index % 3)  # 0 dots, 1 dot, 2 dots, 3 dots
            self.loading_label.config(text="."+dots)
            self.loading_index += 1
            self.loading_animation = self.root.after(1000, self.update_loading)  # Update every 1 second

    def hide_loading(self):
        # Stop animation and remove loading label
        if self.loading_animation:
            self.root.after_cancel(self.loading_animation)
            self.loading_animation = None
        if self.loading_label:
            self.loading_label.destroy()
            self.loading_label = None
        self.loading_index = 0  # Reset index for next loading

    def run_api_request(self, input_text):
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                self.root.after(0, self.handle_api_error, "Gemini API key not found in .env file.")
                return

            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
            headers = {"Content-Type": "application/json"}
            data = {
                "contents": [{"parts": [{
                    "text": "ROLE: You are a flashcard generator. All the flashcard content should be "
                    "generated based on current and official information. "

                    "RESPONSE FORMAT: question|||answer;;;question|||answer;;;question|||answer;;;..."

                    "EXAMPLES: Where is Rome?|||Italy;;;What package would I use for formatted"
                    " I/O?|||fmt;;;How do I call the police?|||Dial 911;;;When is "
                    "Christmas?|||December 25th;;;Who is Jesus?|||The son of God;;;Why is the sky "
                    "blue?|||Rayleigh scattering"
                    
                    "REQUIREMENTS: Always format the response output strictly and exactly. "
                    "Always use simple, clear language and avoid complex terms and definitions. "
                    "Always cover the topic completely and generate as many flashcards as possible. "

                    "All questions must sound like I am asking the question to someone"
                    "All answers must be extremely brief and rememberable. "
                    "If the request is about programming, the preferred progamming language is always Golang. "

                    "Do not label the questions or answers in the response. "
                    "Do not include HTML in the response. "

                    "REQUEST: Generate a verbose and comprehensive list of flashcards about " + input_text + "?"
                    }]}],
                    "generationConfig": {
                    "response_mime_type": "text/plain"
                }
            }

            response = requests.post(f"{url}?key={api_key}", headers=headers, json=data)
            response.raise_for_status()

            # Parse response
            response_data = response.json()
            response_text = response_data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            if not response_text:
                self.root.after(0, self.handle_api_error, "No valid response from API.")
                return

            # Process response in main thread
            self.root.after(0, self.process_input, response_text)

        except requests.exceptions.RequestException as e:
            self.root.after(0, self.handle_api_error, f"API request failed: {str(e)}")
        except json.JSONDecodeError:
            self.root.after(0, self.handle_api_error, "Invalid response format from API.")

    def handle_api_error(self, error_message):
        self.hide_loading()
        self.show_main_frame()
        messagebox.showerror("Error", error_message)

    def submit_to_api(self):
        # Get input text
        input_text = self.text_input.get()
        if not input_text.strip():
            messagebox.showwarning("Warning", "Please enter some text to process!")
            return

        # Show loading animation
        self.show_loading()

        # Run API request in a separate thread
        threading.Thread(target=self.run_api_request, args=(input_text,), daemon=True).start()

    def process_input(self, text):
        # Parse response text into flashcards
        self.flashcards = parse_response_text(text)
        self.hide_loading()  # Remove loading animation
        if not self.flashcards:
            self.show_main_frame()
            messagebox.showwarning("Warning", "No valid flashcards found in API response!")
            return
        self.show_review_page()

    def show_review_page(self):
        # Destroy existing frame
        if hasattr(self, 'main_frame'):
            self.main_frame.destroy()

        # Create main frame for review page
        self.main_frame = tk.Frame(self.root, bg='#2E2E2E')
        self.main_frame.pack(expand=True, fill='both')

        # Create canvas and scrollbar for review page
        self.canvas = tk.Canvas(self.main_frame, width=880, height=480, bg='#2E2E2E', highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.main_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        # Create scrollable frame
        self.scroll_frame = tk.Frame(self.canvas, bg='#2E2E2E')
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")

        # Update scroll region when frame size changes
        self.scroll_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # Bind mouse wheel to scroll
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # Create centered content frame
        content_frame = tk.Frame(self.scroll_frame, bg='#2E2E2E')
        content_frame.pack(expand=True, fill='x', pady=10)

        # Review page content
        tk.Label(content_frame, text="Review New Flashcards", font=("Arial", 14), fg='#E0E0E0', bg='#2E2E2E').pack(pady=10, anchor='center')
        self.check_vars = []
        self.question_entries = []
        self.answer_entries = []

        for i, card in enumerate(self.flashcards):
            # Create a centered frame for each flashcard row
            row_frame = tk.Frame(content_frame, bg='#2E2E2E')
            row_frame.pack(pady=2, anchor='center')

            # Checkbox
            var = tk.BooleanVar(value=True)
            self.check_vars.append(var)
            tk.Checkbutton(row_frame, variable=var, bg='#2E2E2E', fg='white', selectcolor='#4A4A4A').pack(side='left', padx=10)

            # Question and Answer (editable in place)
            tk.Label(row_frame, text="Q:", fg='#E0E0E0', bg='#2E2E2E').pack(side='left', padx=10)
            q_entry = tk.Entry(row_frame, width=85, bg='#4A4A4A', fg='white', insertbackground='white')
            q_entry.insert(0, card['question'])
            q_entry.pack(side='left', padx=10)
            self.question_entries.append(q_entry)

            tk.Label(row_frame, text="A:", fg='#E0E0E0', bg='#2E2E2E').pack(side='left', padx=10)
            a_entry = tk.Entry(row_frame, width=30, bg='#4A4A4A', fg='white', insertbackground='white')
            a_entry.insert(0, card['answer'])
            a_entry.pack(side='left', padx=10)
            self.answer_entries.append(a_entry)

        # Title input with centered text
        tk.Label(content_frame, text="Deck Title:", fg='#E0E0E0', bg='#2E2E2E').pack(pady=10, anchor='center')
        self.title_entry = tk.Entry(content_frame, bg='#4A4A4A', fg='white', insertbackground='white', justify="center")
        self.title_entry.pack(pady=10, anchor='center')

        # Button frame for Create Deck and Back buttons
        button_frame = tk.Frame(content_frame, bg='#2E2E2E')
        button_frame.pack(pady=10, anchor='center')

        # Create deck button
        tk.Button(button_frame, text="Create New Deck", command=self.create_deck, bg='#4A4A4A', fg='white').pack(side='left', padx=10)

        # Back button
        tk.Button(button_frame, text="Back", command=self.return_to_main, bg='#4A4A4A', fg='white').pack(side='left', padx=10)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # TODO: handle FileNotFound Error properly when user enters an invalid deck name.

    def create_deck(self):
        title = self.title_entry.get() or "Untitled Deck"
        selected_flashcards = [
            {'question': self.question_entries[i].get(), 'answer': self.answer_entries[i].get()}
            for i in range(len(self.flashcards)) if self.check_vars[i].get()
        ]
        if not selected_flashcards:
            messagebox.showwarning("Warning", "No flashcards selected!")
            return

        output_path = create_anki_deck(title, selected_flashcards)
        self.canvas.destroy()
        self.scrollbar.destroy()
        self.main_frame.destroy()
        self.main_frame = tk.Frame(self.root, bg='#2E2E2E')
        self.main_frame.pack(expand=True, fill='both')

        # Download page
        tk.Label(self.main_frame, text="Flashcard deck created in Downloads folder!", font=("Arial", 14), fg='#E0E0E0', bg='#2E2E2E').pack(pady=10, anchor='center')
        tk.Button(self.main_frame, text="Return to Home", command=self.return_to_main, bg='#4A4A4A', fg='white').pack(pady=10, anchor='center')

    def return_to_main(self):
        self.show_main_frame()

if __name__ == "__main__":
    root = tk.Tk()
    app = FlashcardApp(root)
    root.mainloop()