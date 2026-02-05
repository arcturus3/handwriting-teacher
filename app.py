import os
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, session, jsonify
import numpy as np
import easyocr
from align import align
from generate import generate_samples

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-prod')

# Character sets for supported languages
ALPHABETS = {
    'en': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
    'ru': 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ',
    'ar': 'ابتثجحخدذرزسشصضطظعغفقكلمنهوي',
}

LANGUAGE_NAMES = {
    'en': 'English',
    'ru': 'Russian',
    'ar': 'Arabic',
}

# EasyOCR language codes
EASYOCR_LANGS = {
    'en': ['en'],
    'ru': ['ru'],
    'ar': ['ar'],
}

# Load all OCR readers at startup
readers = {lang: easyocr.Reader(codes) for lang, codes in EASYOCR_LANGS.items()}


def get_language():
    return session.get('language', 'en')


def get_alphabet():
    return ALPHABETS[get_language()]


def get_scores():
    lang = get_language()
    scores_key = f'scores_{lang}'
    if scores_key not in session:
        session[scores_key] = {c: 0 for c in ALPHABETS[lang]}
    return session[scores_key]


def get_current_sample():
    return session.get('current_sample', '')


def set_current_sample(sample):
    session['current_sample'] = sample


@app.route("/")
def index():
    return app.send_static_file("index.html")


@app.route('/language', methods=['GET'])
def get_lang():
    return jsonify({
        'language': get_language(),
        'alphabet': get_alphabet(),
        'name': LANGUAGE_NAMES[get_language()],
        'available': list(LANGUAGE_NAMES.keys()),
    })


@app.route('/language', methods=['POST'])
def set_language():
    data = request.get_json()
    lang = data.get('language', 'en')
    if lang in ALPHABETS:
        session['language'] = lang
        session.modified = True
    return jsonify({
        'language': get_language(),
        'alphabet': get_alphabet(),
        'name': LANGUAGE_NAMES[get_language()],
        'scores': get_scores(),
    })


@app.route('/sample', methods=['GET'])
def get_sample():
    lang = get_language()
    scores = get_scores()
    chars = np.array(list(scores.keys()))
    weights = np.array([1 - score for score in scores.values()])
    if np.sum(weights) == 0:
        weights = np.ones_like(weights) / weights.shape[0]
    else:
        weights = weights / np.sum(weights)
    weighted_chars = list(np.random.choice(chars, min(4, len(chars)), replace=False, p=weights))
    sample = generate_samples(1, 4, weighted_chars, lang)[0]
    set_current_sample(sample)
    return sample


@app.route("/submit_canvas", methods=["POST"])
def submit_canvas():
    canvas = request.files["imageFile"].read()
    current_sample = get_current_sample()
    trimmed_sample = current_sample.replace(" ", "")
    recognized_input = recognize_canvas(canvas)

    scores = get_scores()
    success_chars = generate_score(recognized_input, trimmed_sample, scores)

    lang = get_language()
    session[f'scores_{lang}'] = scores
    session.modified = True

    return jsonify({
        'scores': scores,
        'successful': success_chars
    })


def recognize_canvas(image_data) -> list[tuple[str, float]]:
    lang = get_language()
    reader = readers[lang]
    result = reader.readtext(image_data)
    return [(each[1], each[2]) for each in result]


def generate_score(
        recognized_input: list[tuple[str, float]], trimmed_sample: str, scores: dict
) -> list[str]:
    lang = get_language()
    trimmed_input = "".join(text for text, _ in recognized_input)
    confidence_for_each_input_letter = [
        confidence for text, confidence in recognized_input for _ in text
    ]

    text_presence = align(trimmed_sample, trimmed_input)

    confidence_threshold = 0.6
    practice_threshold = 4

    success_chars = set()
    input_index = 0
    for i, letter in enumerate(trimmed_sample):
        if text_presence[i]:
            # For English/Russian, normalize case. Arabic has no case.
            normalized = letter.upper() if lang in ['en', 'ru'] else letter
            if normalized in scores and input_index < len(confidence_for_each_input_letter):
                if confidence_for_each_input_letter[input_index] > confidence_threshold:
                    scores[normalized] = min(1, scores[normalized] + 1 / practice_threshold)
                    success_chars.add(normalized)
            input_index += 1

    return list(success_chars)


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5123))
    app.run(host='0.0.0.0', port=port)
