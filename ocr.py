"""Reads the handwriting canvas with PaddleOCR.

Chosen by a benchmark on real handwriting (IAM English lines, KHATT Arabic lines, Russian
words), 2 CPU threads. Character error rate and median time per image, against EasyOCR:
English 0.35 at 221 ms (EasyOCR 0.63 at 535 ms), Arabic 0.60 at 279 ms (0.75 at 1,177 ms),
Russian 0.76 (0.82). PP-OCRv6 reads no Arabic or Cyrillic, so those use PP-OCRv5's models.
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
        )
    return _readers[lang]


def load_all() -> None:
    """Loads every language's models, so the first submission isn't slow."""
    for lang in RECOGNITION_MODELS:
        reader(lang)


def recognize(image_data: bytes, lang: str) -> list[tuple[str, float]]:
    """Each line of text read from the image, in reading order, with its confidence (0 to 1)."""
    image = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError('The canvas image could not be decoded.')
    lines: list[tuple[str, float]] = []
    for page in reader(lang).predict(image):
        for text, score in zip(page['rec_texts'], page['rec_scores']):
            if text.strip():
                lines.append((str(text), float(score)))
    return lines
