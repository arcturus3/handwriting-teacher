from collections import defaultdict
from string import ascii_uppercase
from flask import Flask, request
import numpy as np
import easyocr
from align import align
from generate import generate_samples

app = Flask(__name__)
app.debug = True
reader = easyocr.Reader(["en"])

scores = {c: 0 for c in ascii_uppercase}


@app.route("/")
def index():
    return app.send_static_file("index.html")


@app.route('/sample', methods=['GET'])
def get_sample():
    chars = np.array(list(scores.keys()))
    weights = np.array([1 - score for score in scores.values()])
    if np.sum(weights) == 0:
        weights = np.ones_like(weights) / weights.shape[0]
    else:
        weights = weights / np.sum(weights)
    weighted_chars = list(np.random.choice(chars, 4, replace=False, p=weights))
    samples = generate_samples(1, 4, weighted_chars)
    return samples[0]


@app.route("/submit_canvas", methods=["POST"])
def submit_canvas():
    canvas = request.files["imageFile"].read()

    sample: str = request.form["sample"]
    trimmed_sample = sample.replace(" ", "")

    recognized_input = recognize_canvas(canvas)

    return generate_score(recognized_input, trimmed_sample)


def recognize_canvas(image_data) -> list[tuple[str, float]]:
    result = reader.readtext(image_data)
    return [(each[1], each[2]) for each in result]


def generate_score(
    recognized_input: list[tuple[str, float]], trimmed_sample: str
) -> dict[str, int]:
    trimmed_input = "".join(text for text, _ in recognized_input)
    confidence_for_each_input_letter = [
        confidence for text, confidence in recognized_input for _ in text
    ]

    text_presence = align(trimmed_sample, trimmed_input)

    confidence_threshold = 0.6

    scoring = defaultdict(int)
    input_index = 0
    for i, letter in enumerate(trimmed_sample):
        if text_presence[i]:
            input_index += 1
            if confidence_for_each_input_letter[input_index] > confidence_threshold:
                scoring[letter] += 1

    return scoring


app.run()
