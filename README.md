<h1 style="color:#ff6a00;">
  VAANI – Where Every Book Finds a Voice
</h1>



VAANI is an AI-powered web application that transforms PDF documents into simplified study notes, generates audio summaries, and allows users to ask questions about the uploaded document.

It is designed with accessibility, voice control, and inclusive learning in mind.

🚀 Features
📄 PDF Processing

Upload any PDF document

Extract original text

Generate simplified study notes

Multi-language support (English, Hindi, Kannada)

🎧 Audio Summary

Automatically generates an audio version of the summary

Built-in audio player

💬 Document Q&A

Ask questions related to the uploaded document

Interactive chat interface

Context-based AI answers

♿ Accessibility Features

Dyslexia-friendly font mode (OpenDyslexic)

Adjustable font size (A- / A+)

Background color customization

Clean and readable UI

🎙 Voice Control

Scroll up / down

Focus next / previous element

Select elements

Read aloud content

Stop voice mode

🎨 Theme Modes

Calm

Sunset

Night

🖥 Project Structure
├── index.html      # Main application page (PDF upload + results)
├── qa.html         # Q&A chat interface
├── /outputs        # Generated audio files (server side)
└── README.md

⚙️ How It Works

User uploads a PDF.

Backend processes the file.

The app:

Extracts original text

Generates simplified notes

Creates an audio summary

User can:

Switch between original & simplified text

Adjust accessibility settings

Ask questions about the document

🛠 Technologies Used

HTML5

CSS3 (Glassmorphism UI + Animations)

JavaScript (Vanilla JS)

Web Speech API (Voice recognition & synthesis)

Fetch API (Async communication)

Google Fonts (Poppins)

OpenDyslexic Font

<img width="1345" height="598" alt="image" src="https://github.com/user-attachments/assets/80537c5e-193d-4eca-b944-55263de0540c" />

🔧 Setup Instructions (Basic)

Clone the repository:

git clone https://github.com/your-username/vaani.git


Add backend server (Flask / Node / etc.)

Run your backend server:

python app.py


Open in browser:

http://localhost:5000

🌟 Future Improvements

More language support

PDF highlighting

Downloadable notes

Voice-based Q&A

User login system

Cloud deployment

👨‍💻 Author

Sumit Kumar Singh

If you like this project, give it a ⭐ on GitHub!
