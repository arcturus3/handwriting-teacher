from collections import defaultdict

import cv2
import easyocr
import numpy as np
from flask import Flask, request

import sample_gen

app = Flask(__name__)
reader = easyocr.Reader(['en'])


@app.route('/get_sample', methods=['POST'])
def get_sample():
    scores = request.get_json()["scores"]
    word_count = request.get_json()["word_count"] or 1
    letters = []
    weights = []
    for letter, score in scores:
        letters.append(letter)
        weights.append(1 / score)
    prioritized_letters = np.random.choice(letters, 5, replace=False, p=weights)
    return sample_gen.generate_samples(5, word_count, prioritized_letters)


@app.route('/submit_canvas', methods=['POST'])
def submit_canvas():
    data = request.get_json()
    canvas = data["canvas"]
    sample: str = data["sample"]
    trimmed_sample = sample.replace(" ", "")

    recognized_input = recognize_canvas(canvas)

    return generate_score(recognized_input, trimmed_sample)


def recognize_canvas(image_data) -> list[tuple[str, float]]:
    img = cv2.imread(image_data)
    result = reader.readtext(img)
    return [(text, score) for each in result for text, score in each[1:]]


def generate_score(recognized_input: list[tuple[str, float]], trimmed_sample: str) -> dict[str, int]:
    trimmed_input = "".join(text for text, _ in recognized_input)
    confidence_for_each_input_letter = [confidence for text, confidence in recognized_input for _ in text]

    text_presence = check_text_presence(trimmed_input, trimmed_sample)

    confidence_threshold = 0.6

    scoring = defaultdict(int)
    input_index = 0
    for i, letter in trimmed_sample:
        if text_presence[i]:
            input_index += 1
            if confidence_for_each_input_letter[input_index] > confidence_threshold:
                scoring[letter] += 1

    return scoring


def check_text_presence(trimmed_input: str, trimmed_sample: str) -> list[bool]:
    pass
