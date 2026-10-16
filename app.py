import os
import time
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, has_request_context, request, session, jsonify
import numpy as np
import analytics
import ocr
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

# Load every language's OCR models at startup
ocr.load_all()



def requesting_browser() -> analytics.Client | None:
    """The browser whose request is being handled, so its events join its visit in Umami."""
    return analytics.client_from_headers(request.headers.get) if has_request_context() else None


track: analytics.Track = (
    analytics.tracker_from_env(os.environ, requesting_browser) or (lambda name, data: None)
)


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
        'scores': get_scores(),
        'available': list(LANGUAGE_NAMES.keys()),
    })


@app.route('/language', methods=['POST'])
def set_language():
    data = request.get_json()
    lang = data.get('language', 'en')
    if lang in ALPHABETS:
        session['language'] = lang
        session.modified = True
        track('language-changed', {'language': lang})
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
    started = time.monotonic()
    try:
        sample = generate_samples(1, 4, weighted_chars, lang)[0]
    except Exception as error:
        track('sentence-failed', {'language': lang, 'error': type(error).__name__})
        raise
    track('sentence-generated', {'language': lang, 'ms': round((time.monotonic() - started) * 1000)})
    set_current_sample(sample)
    return sample


@app.route("/submit_canvas", methods=["POST"])
def submit_canvas():
    canvas = request.files["imageFile"].read()
    current_sample = get_current_sample()
    trimmed_sample = current_sample.replace(" ", "")
    started = time.monotonic()
    recognized_input = recognize_canvas(canvas)
    ocr_ms = round((time.monotonic() - started) * 1000)

    scores = get_scores()
    char_results = generate_score(recognized_input, trimmed_sample, current_sample, scores)

    lang = get_language()
    session[f'scores_{lang}'] = scores
    session.modified = True

    # Counts only: nothing the learner wrote or was asked to write is sent.
    track('submission-scored', {
        'language': lang,
        'letters': len(trimmed_sample),
        'matched': sum(1 for result in char_results if result),
        'read_anything': bool(recognized_input),
        'ocr_ms': ocr_ms,
    })

    return jsonify({
        'scores': scores,
        'sample': current_sample,
        'char_results': char_results,
    })


def recognize_canvas(image_data: bytes) -> list[tuple[str, float]]:
    return ocr.recognize(image_data, get_language())


def generate_score(
        recognized_input: list[tuple[str, float]], trimmed_sample: str, original_sample: str, scores: dict
) -> list:
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
            normalized = letter.upper() if lang in ['en', 'ru'] else letter
            if normalized in scores and input_index < len(confidence_for_each_input_letter):
                if confidence_for_each_input_letter[input_index] > confidence_threshold:
                    scores[normalized] = min(1, scores[normalized] + 1 / practice_threshold)
                    success_chars.add(normalized)
            input_index += 1

    # Map text_presence back to original sample (with spaces)
    char_results = []
    ti = 0
    for ch in original_sample:
        if ch == ' ':
            char_results.append(None)
        else:
            char_results.append(text_presence[ti] if ti < len(text_presence) else False)
            ti += 1

    return char_results


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5123))
    app.run(host='0.0.0.0', port=port)
