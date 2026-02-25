from flask import Flask, render_template, request, jsonify
import cv2
import numpy as np
import easyocr
import os
import re
import base64
from io import BytesIO
from gtts import gTTS
from deep_translator import GoogleTranslator
from werkzeug.utils import secure_filename

# ---------------- APP SETUP ----------------

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5MB

# Initialize OCR ONCE
reader = easyocr.Reader(['en'], gpu=False)

LANGUAGE_CODES = {
    "English": "en",
    "Hindi": "hi",
    "Kannada": "kn",
    "Telugu": "te",
    "Tamil": "ta"
}

# ---------------- UTILITIES ----------------

def resize_image(img, max_width=1000):
    h, w = img.shape[:2]
    if w > max_width:
        scale = max_width / w
        img = cv2.resize(img, None, fx=scale, fy=scale)
    return img


def clean_text(text):
    text = re.sub(r'[^A-Za-z0-9.,!?\'" ]+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# ---------------- PREPROCESSING ----------------

def preprocess_printed(image_path):
    img = cv2.imread(image_path)
    img = resize_image(img)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return gray


def preprocess_handwritten(image_path):
    """
    Best compromise preprocessing:
    - Preserves thin strokes
    - Works for light handwriting
    - Does not destroy cursive
    """
    img = cv2.imread(image_path)
    img = resize_image(img)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Mild contrast enhancement
    gray = cv2.convertScaleAbs(gray, alpha=1.2, beta=10)

    # Light smoothing (do NOT over-blur)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)

    return blur

# ---------------- ROUTES ----------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/process", methods=["POST"])
def process():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"})

    image = request.files["image"]
    mode = request.form.get("mode", "printed")
    language = request.form.get("language", "English")

    if image.filename == "":
        return jsonify({"error": "No selected image"})

    filename = secure_filename(image.filename)
    image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    image.save(image_path)

    try:
        # Choose preprocessing
        if mode == "handwritten":
            processed = preprocess_handwritten(image_path)
        else:
            processed = preprocess_printed(image_path)

        # EasyOCR expects RGB
        processed_rgb = cv2.cvtColor(processed, cv2.COLOR_GRAY2RGB)

        # OCR (balanced parameters)
        result = reader.readtext(
            processed_rgb,
            paragraph=True,
            detail=0,
            text_threshold=0.7,
            low_text=0.4,
            link_threshold=0.5
        )

        extracted_text = clean_text(" ".join(result))

        if len(extracted_text) < 5:
            return jsonify({
                "error": "Text could not be detected clearly. Please upload a clearer image."
            })

        # Translation
        target_lang = LANGUAGE_CODES.get(language, "en")
        translated_text = GoogleTranslator(
            source="en",
            target=target_lang
        ).translate(extracted_text)

        # -------- AUDIO (IN MEMORY ONLY) --------
        audio_buffer = BytesIO()
        tts = gTTS(text=translated_text, lang=target_lang)
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)

        audio_base64 = base64.b64encode(audio_buffer.read()).decode("utf-8")
        del audio_buffer

        return jsonify({
            "extracted_text": extracted_text,
            "translated_text": translated_text,
            "audio_base64": audio_base64
        })

    except Exception as e:
        return jsonify({"error": str(e)})

    finally:
        # Clean uploaded image
        if os.path.exists(image_path):
            os.remove(image_path)


if __name__ == "__main__":
    app.run(debug=True)