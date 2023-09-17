from collections import defaultdict

import easyocr
import numpy as np
from flask import Flask, request

import sample_gen
from align import align as check_text_presence

app = Flask(__name__)
app.debug = True
reader = easyocr.Reader(['en'])


@app.route('/')
def index():
    return app.send_static_file('index.html')


@app.route('/get_sample', methods=['POST'])
def get_sample():
    scores = request.get_json()["scores"]
    word_count = request.get_json()["word_count"] or 1
    letters = []
    weights = []
    for letter, score in scores:
        letters.append(letter)
        weights.append(1 / score)
    prioritized_letters = list(np.random.choice(letters, 5, replace=False, p=weights))
    return sample_gen.generate_samples(5, word_count, prioritized_letters)


@app.route('/submit_canvas', methods=['POST'])
def submit_canvas():
    print(request)
    canvas = request.files['imageFile'].read()

    sample: str = request.form["sample"]
    trimmed_sample = sample.replace(" ", "")

    recognized_input = recognize_canvas(canvas)

    return generate_score(recognized_input, trimmed_sample)


def recognize_canvas(image_data) -> list[tuple[str, float]]:
    result = reader.readtext(image_data)
    return [(each[1], each[2]) for each in result]


def generate_score(recognized_input: list[tuple[str, float]], trimmed_sample: str) -> dict[str, int]:
    trimmed_input = "".join(text for text, _ in recognized_input)
    confidence_for_each_input_letter = [confidence for text, confidence in recognized_input for _ in text]

    text_presence = check_text_presence(trimmed_input, trimmed_sample)

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
