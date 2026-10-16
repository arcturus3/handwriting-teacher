"""Reads the handwriting canvas with PaddleOCR.

Chosen by a benchmark on real handwriting (IAM English lines, KHATT Arabic lines, Russian
words), 2 CPU threads. Character error rate and median time per image, against EasyOCR:
English 0.21 at 100 ms (EasyOCR 0.63 at 535 ms), Arabic 0.63 at 164 ms (0.75 at 1,177 ms),
Russian 0.77 (0.82). PP-OCRv6 reads no Arabic or Cyrillic, so those use PP-OCRv5's models.
"""
import os

import cv2
import numpy as np
from paddleocr import PaddleOCR

DETECTION_MODEL = 'PP-OCRv5_mobile_det'
RECOGNITION_MODELS = {
    'en': 'PP-OCRv6_small_rec',
    'ru': 'eslav_PP-OCRv5_mobile_rec',
    'ar': 'arabic_PP-OCRv5_mobile_rec',
}
CPU_THREADS = int(os.getenv('OCR_CPU_THREADS', '2'))
# Detection shrinks the image so its longer side is at most this. A high-density canvas is
# 2,000 to 2,800 pixels wide with letters hundreds of pixels tall, which the detector misses
# letters of and breaks into specks. On the benchmark this cut English CER from 0.30 to 0.21
# and halved the time, with Arabic and Russian unchanged.
DETECTION_MAX_SIDE = 960
# The detector also misses letters much taller than the scanned handwriting it reads well,
# whose letters are about 42 pixels tall. Writing on the canvas runs to 240 and beyond, so
# detection shrinks the image further until its letters are about this tall. Images with
# smaller letters, like the benchmark's, aren't shrunk any further.
DETECTION_LETTER_HEIGHT = 64
# The shrink stops here, so a bad height estimate (a shadow in a photo read as ink) can't
# shrink an image to nothing.
DETECTION_MIN_SIDE = 480
# Ink blobs smaller than this many pixels are specks, not letters.
MIN_LETTER_AREA = 30

_readers: dict[str, PaddleOCR] = {}


def reader(lang: str) -> PaddleOCR:
    if lang not in _readers:
        _readers[lang] = PaddleOCR(
            text_detection_model_name=DETECTION_MODEL,
            text_recognition_model_name=RECOGNITION_MODELS[lang],
            # The canvas is always upright and flat.
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            device='cpu',
            cpu_threads=CPU_THREADS,
            # Paddle 3.3's oneDNN path fails on x86 with "ConvertPirAttribute2RuntimeAttribute
            # not support", so run plain CPU kernels.
            enable_mkldnn=False,
            text_det_limit_side_len=DETECTION_MAX_SIDE,
            text_det_limit_type='max',
        )
    return _readers[lang]


def load_all() -> None:
    """Loads every language's models, so the first submission isn't slow."""
    for lang in RECOGNITION_MODELS:
        reader(lang)


# A box joins a line when at least this much of its height overlaps the line's.
LINE_OVERLAP = 0.3

Box = tuple[float, float, float, float]  # left, top, right, bottom


def reading_order(boxes: list[Box]) -> list[int]:
    """Indexes of the boxes in reading order: lines top to bottom, each left to right.

    Paddle finds each handwritten word on its own and orders them top to bottom, so a word
    written a little higher jumps ahead of the words before it. A line's span grows with each
    word it takes, so writing that wanders up or down stays one line.
    """
    lines: list[tuple[float, float, list[int]]] = []  # top, bottom, members
    for i in sorted(range(len(boxes)), key=lambda i: boxes[i][1]):
        _, top, _, bottom = boxes[i]
        height = max(bottom - top, 1.0)
        for n, (line_top, line_bottom, members) in enumerate(lines):
            if min(bottom, line_bottom) - max(top, line_top) >= LINE_OVERLAP * height:
                lines[n] = (min(top, line_top), max(bottom, line_bottom), members + [i])
                break
        else:
            lines.append((top, bottom, [i]))
    lines.sort(key=lambda line: line[0])
    return [i for _, _, members in lines for i in sorted(members, key=lambda i: boxes[i][0])]


def letter_height(image: np.ndarray) -> float | None:
    """The median height of the ink's blobs, roughly a letter's height; None with no ink."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, ink = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    count, _, stats, _ = cv2.connectedComponentsWithStats(ink, connectivity=8)
    heights = [
        int(stats[i, cv2.CC_STAT_HEIGHT]) for i in range(1, count)
        if stats[i, cv2.CC_STAT_AREA] >= MIN_LETTER_AREA
    ]
    return float(np.median(heights)) if heights else None


def detection_side(image: np.ndarray) -> int:
    """The longest side the detector should see this image at."""
    longest = max(image.shape[:2])
    height = letter_height(image)
    scale = min(1.0, DETECTION_LETTER_HEIGHT / height) if height else 1.0
    return int(min(DETECTION_MAX_SIDE, max(DETECTION_MIN_SIDE, longest * scale)))


def recognize(image_data: bytes, lang: str) -> list[tuple[str, float]]:
    """Each piece of text read from the image, in reading order, with its confidence (0 to 1)."""
    image = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError('The canvas image could not be decoded.')
    pieces: list[tuple[str, float]] = []
    for page in reader(lang).predict(
            image, text_det_limit_side_len=detection_side(image), text_det_limit_type='max'):
        boxes: list[Box] = [(float(l), float(t), float(r), float(b)) for l, t, r, b in page['rec_boxes']]
        for i in reading_order(boxes):
            text = str(page['rec_texts'][i])
            if text.strip():
                pieces.append((text, float(page['rec_scores'][i])))
    return pieces
