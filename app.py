import random

import easyocr
import numpy as np
from flask import Flask, render_template, request, send_file, make_response
import cv2
import sample

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
    return sample.generate_samples(5, word_count, prioritized_letters)


@app.route('/submit_canvas', methods=['POST'])
def submit_canvas():
    data = request.get_json()
    canvas = data["canvas"]
    sample: str = data["sample"]
    trimmed_sample = sample.replace(" ", "")

    translated_text = recognize_canvas(data)

    return generate_score(translated_text, trimmed_sample)


def recognize_canvas(matrix: list[list[float]]) -> dict[str, float]:
    img = cv2.imread('input_2.jpg')
    result = reader.readtext(img)

    # Create a dictionary of possible combinations and their confidence scores
    # combinations = []`
    # for each in result:
    #     for text, score in each[1:]:
    #         combinations.append((text, score))


# Still working this out
#
# return possible_combinations


def generate_score(possible_combinations, sample):
    score_list = []
    for l in sample:
        if l in possible_combinations:
            score_list.append((l, possible_combinations[l]))
        else:
            score_list.append((l, 0))

    return score_list
