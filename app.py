import os
from string import ascii_uppercase
from flask import Flask, request, session
import numpy as np
import easyocr
from align import align
from generate import generate_samples

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-prod')
reader = easyocr.Reader(["en"])


def get_scores():
    if 'scores' not in session:
        session['scores'] = {c: 0 for c in ascii_uppercase}
    return session['scores']


def get_current_sample():
    return session.get('current_sample', '')


def set_current_sample(sample):
    session['current_sample'] = sample


@app.route("/")
def index():
    return app.send_static_file("index.html")


@app.route('/sample', methods=['GET'])
def get_sample():
    scores = get_scores()
    chars = np.array(list(scores.keys()))
    weights = np.array([1 - score for score in scores.values()])
    if np.sum(weights) == 0:
        weights = np.ones_like(weights) / weights.shape[0]
    else:
        weights = weights / np.sum(weights)
    weighted_chars = list(np.random.choice(chars, 4, replace=False, p=weights))
    sample = generate_samples(1, 4, weighted_chars)[0]
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
    session['scores'] = scores  # Mark session as modified
    session.modified = True

    return {
        'scores': scores,
        'successful': success_chars
    }


def recognize_canvas(image_data) -> list[tuple[str, float]]:
    result = reader.readtext(image_data)
    return [(each[1], each[2]) for each in result]


def generate_score(
        recognized_input: list[tuple[str, float]], trimmed_sample: str, scores: dict
) -> list[str]:
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
            if letter.upper() in scores and confidence_for_each_input_letter[input_index] > confidence_threshold:
                scores[letter.upper()] = min(1, scores[letter.upper()] + 1 / practice_threshold)
                success_chars.add(letter.upper())
            input_index += 1

    return list(success_chars)


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5123))
    app.run(host='0.0.0.0', port=port)
