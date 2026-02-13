import os
import re
import logging
import uuid
import threading
from flask import Flask, request, render_template, redirect, url_for, send_from_directory, jsonify
from werkzeug.utils import secure_filename
import pytesseract
import fitz  # PyMuPDF
from PIL import Image
from gtts import gTTS
import google.generativeai as genai

# ========================
# --- CONFIGURATION ---
# ========================

logging.getLogger("pytesseract").setLevel(logging.ERROR)

# 🔑 TEMP: directly set your new API key here
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("⚠️ WARNING: GEMINI_API_KEY environment variable not set.")
    # Fallback for development, but not recommended for production
    API_KEY = "AIzaSyB5TyUTl3wJvglXvaIuvNx9fmzIYpLwZTA" 


try:
    genai.configure(api_key=API_KEY)
    print("✅ Google AI SDK configured successfully.")
except Exception as e:
    print(f"❌ Error configuring Google AI SDK: {e}")

try:
    model = genai.GenerativeModel("gemini-2.5-pro")
    print("✅ Using model: gemini-2.5-pro")	
except Exception:
    print("⚠️ gemini-2.5-pro unavailable — falling back to gemini-2.5-flash.")
    model = genai.GenerativeModel("gemini-2.5-flash")


UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
ALLOWED_EXTENSIONS = {'pdf'}

try:
    TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(TESSERACT_PATH):
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
except Exception:
    print("Tesseract executable not found at specified path. Ensure it's installed and the path is correct if you're on Windows.")


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

tasks = {}

# ========================
# --- CORE FUNCTIONS ---
# ========================

def extract_text_from_pdf(pdf_path, task_id):
    tasks[task_id]['status'] = 'Processing... (Step 1/3: Extracting Text)'
    tasks[task_id]['progress'] = 15
    full_text = ""
    try:
        doc = fitz.open(pdf_path)
        matrix = fitz.Matrix(3, 3)
        total_pages = len(doc)
        for page_num in range(total_pages):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(matrix=matrix)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img = img.convert("L")
            page_text = pytesseract.image_to_string(img)
            full_text += page_text + "\n\n"
            tasks[task_id]['progress'] = 15 + int(40 * (page_num + 1) / total_pages)
        doc.close()
    except Exception as e:
        print(f"❌ Error during OCR: {e}")
        return f"An error occurred during text extraction: {e}"
    return full_text

def simplify_text(text, language, task_id):
    tasks[task_id]['status'] = 'Processing... (Step 2/3: Generating AI Notes)'
    tasks[task_id]['progress'] = 60
    if not text or not text.strip():
        return "⚠️ No readable text was extracted from the PDF."

    prompt = f"""
Your single most important job is to make the text below extremely easy to understand for someone who finds reading difficult.

First, translate the text into **{language}**. Then, rewrite it in that language following these strict rules:

1.  **Use Simple Words:** Use common, everyday words only.
2.  **Short Sentences:** Keep every sentence very short.
3.  **One Idea Per Sentence:** Each sentence should only have one main idea.
4.  **Explain Big Words:** If you must use a complicated word, explain it right away in parentheses (like this).
5.  **Use Analogies:** If possible, use a simple analogy or example to explain the main point.
6.  **Focus on "What" and "Why":** Explain what the text is about and why it matters in the simplest way possible.

Do not try to sound academic or formal. Your tone should be encouraging and very clear.

Text to process:
---
{text}
---
"""
    try:
        if not model:
            return "⚠️ AI Model is not configured. Cannot simplify text."
        response = model.generate_content(prompt)
        tasks[task_id]['progress'] = 85
        return response.text
    except Exception as e:
        print(f"❌ AI simplification error: {e}")
        return f"⚠️ Could not simplify text due to AI service error: {e}"

def convert_text_to_speech(text, output_filename, lang_code, task_id):
    tasks[task_id]['status'] = 'Processing... (Step 3/3: Creating Audio File)'
    tasks[task_id]['progress'] = 90
    try:
        speech_text = re.sub(r'[\*#✅→🧠🔬💡]', '', text)
        tts_text = ' '.join(speech_text.split()[:500])
        if not tts_text.strip(): return None

        tts = gTTS(text=tts_text, lang=lang_code, slow=False)
        filepath = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        tts.save(filepath)
        tasks[task_id]['progress'] = 100
        return output_filename
    except Exception as e:
        print(f"❌ Error in TTS: {e}")
        return None

def process_file_in_background(filepath, language, filename, task_id):
    try:
        extracted_text = extract_text_from_pdf(filepath, task_id)
        if "An error occurred" in extracted_text or not extracted_text.strip():
            tasks[task_id]['status'] = 'Error'
            tasks[task_id]['result'] = {'original_text': extracted_text, 'simplified_text': "Could not extract readable text from the PDF."}
            return

        simplified_text = simplify_text(extracted_text, language, task_id)

        lang_codes = {'English': 'en', 'Hindi': 'hi', 'Kannada': 'kn'}
        lang_code = lang_codes.get(language, 'en')
        base_filename = filename.rsplit('.', 1)[0]
        audio_filename = f"{base_filename}_{lang_code}.mp3"
        convert_text_to_speech(simplified_text, audio_filename, lang_code, task_id)

        tasks[task_id]['status'] = 'Complete'
        tasks[task_id]['result'] = {'original_text': extracted_text, 'simplified_text': simplified_text, 'audio_file': audio_filename}
    except Exception as e:
        print(f"❌ Background task failed: {e}")
        tasks[task_id]['status'] = 'Error'
        tasks[task_id]['result'] = {'original_text': f"An unexpected error occurred: {e}", 'simplified_text': f"An unexpected error occurred: {e}"}

# ========================
# --- FLASK ROUTES ---
# ========================

@app.route('/', methods=['GET'])
def index():
    task_id = request.args.get('task_id')
    if task_id and task_id in tasks and tasks[task_id].get('status') == 'Complete':
        task = tasks[task_id]
        return render_template('index.html', task_id=task_id, result=task.get('result'))
    return render_template('index.html', task_id=None, result=None)

@app.route('/upload', methods=['POST'])
def upload_file_route():
    if 'file' not in request.files: return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '': return jsonify({'error': 'No selected file'}), 400

    if file and '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        language = request.form.get('language', 'English')
        task_id = str(uuid.uuid4())
        tasks[task_id] = {'status': 'Queued', 'progress': 0}

        thread = threading.Thread(target=process_file_in_background, args=(filepath, language, filename, task_id))
        thread.start()

        return jsonify({'task_id': task_id})
    return jsonify({'error': 'Invalid file type. Please upload a PDF.'}), 400

@app.route('/status/<task_id>')
def task_status(task_id):
    return jsonify(tasks.get(task_id, {}))

@app.route('/outputs/<filename>')
def serve_output_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

# --- NEW Q&A ROUTES ---
@app.route('/qa/<task_id>')
def qa_page(task_id):
    """Renders the Q&A chat page for a specific task."""
    if task_id not in tasks or tasks[task_id].get('status') != 'Complete':
        return redirect(url_for('index'))
    return render_template('qa.html', task_id=task_id)

@app.route('/ask', methods=['POST'])
def ask_question():
    """Handles a question about a document and returns an AI-generated answer."""
    data = request.get_json()
    task_id = data.get('task_id')
    question = data.get('question')

    if not task_id or not question:
        return jsonify({'error': 'Missing task_id or question'}), 400

    task = tasks.get(task_id)
    if not task or task.get('status') != 'Complete':
        return jsonify({'answer': 'Sorry, the document context is not available or still processing.'}), 404

    document_context = task['result'].get('original_text')
    if not document_context:
        return jsonify({'answer': 'Could not find the text for this document.'}), 404

    prompt = f"""
You are a helpful assistant. Your job is to answer the user's question based ONLY on the provided document text.
If the answer is not in the text, say "I couldn't find an answer to that in the document." Do not use any external knowledge.

--- DOCUMENT TEXT ---
{document_context}
--- END DOCUMENT TEXT ---

User's Question: {question}
"""
    try:
        if not model:
            return jsonify({'answer': 'The AI model is not available.'}), 500
        response = model.generate_content(prompt)
        answer = response.text
    except Exception as e:
        print(f"❌ AI Q&A error: {e}")
        answer = "Sorry, I encountered an error while trying to find the answer."
    
    return jsonify({'answer': answer})


# ========================
# --- MAIN ENTRY POINT ---
# ========================
if __name__ == '__main__':
    app.run(debug=True)