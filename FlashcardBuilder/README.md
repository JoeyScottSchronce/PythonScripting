## Flashcard Builder
A Python application built with Tkinter that generates flashcards using the Gemini API and exports them as Anki decks for efficient studying.

## Features
- Generate quiz questions and answers for any topic via the Gemini API
- Review, edit, and select flashcards in a scrollable GUI
- Export selected flashcards as an Anki .apkg file to the Downloads folder
- Dark-themed, responsive interface with loading animation
- Error handling for invalid inputs or API issues

## Requirements
- Python 3.7+
- tkinter (included with Python)
- requests
- genanki
- python-dotenv
- threading (standard library, included with Python)

## Installation
Fork the repository:
1. Fork this repository on GitHub to create your own copy for customization or contribution.

2. Install the required packages:Open a terminal and run:
```
pip install requests genanki python-dotenv pyinstaller
```

3. Configure environment variables:  

- Create a .env file in the project root.  
- Add your Gemini API key (obtain from Google AI Platform):
```
GEMINI_API_KEY=your_gemini_api_key_here
```

4. Make any changes you wish to personalize the UI or functionality in an IDE, then continue to Usage.


## Usage

1. Save the file as a .py file with pyinstaller.
```
pyinstaller --onefile flashcard_builder.py
```

2. Create a shortcut on your desktop to run the software. Your "Target" will resemble this filepath:  
```
"C:\Program Files\Python37\pythonw.exe" "C:\Users\<Username>\<path to saved file>\dist\flashcard_builder.exe"
```

This will create a standalone executable without a console window. Change the icon and other details to suit your needs.

3. Run the application with the new shortcut.


## How to use the GUI:
- Enter a topic (e.g., "World History") in the text field and click "Generate" to fetch questions from the Gemini API.  
- Review the generated flashcards in the scrollable list; edit questions or answers directly.  
- Uncheck any flashcards you don’t want to include in the deck.  
- Enter a deck title in the provided field (defaults to "Untitled Deck" if blank).  
- Click "Create New Deck" to save the .apkg file to your Downloads folder.  
- Click "Back" to return to the main screen or "Return to Home" after deck creation.  
- Import the .apkg file into Anki to start studying.

## Notes
- A valid Gemini API key is required in the .env file.  
- Decks are saved to the user's Downloads folder.  
- Ensure Anki is installed to import .apkg files.  
- API requests run in a separate thread for a smooth GUI experience.

## Acknowledgments
- Python
- Tkinter
- Genanki
- Requests
- python-dotenv

