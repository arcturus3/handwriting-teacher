import easyocr
from flask import Flask, render_template, request, send_file, make_response
import cv2
import sample

app = Flask(__name__)
reader = easyocr.Reader(['en'])


@app.route('/get_sample')
def get_sample():
    return sample.generate_samples(5, 5, )


def generate_sample(word_count: int, letter_weights: dict[str, float]) -> str:
    pass


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


print(recognize_canvas([
    [0, 1, 0, 0, 0],
    [0, 1, 0, 0, 0],
    [0, 1, 0, 0, 0],
    [0, 1, 0, 0, 0],
    [0, 1, 1, 1, 0]
]))


def generate_score(possible_combinations, sample):
    score_list = []
    for l in sample:
        if l in possible_combinations:
            score_list.append((l, possible_combinations[l]))
        else:
            score_list.append((l, 0))

    return score_list
