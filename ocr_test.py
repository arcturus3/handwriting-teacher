import io

from PIL import Image, ImageDraw, ImageFont

import ocr


def test_each_language_reads_with_the_model_that_won_the_benchmark() -> None:
    assert ocr.RECOGNITION_MODELS == {
        'en': 'PP-OCRv6_small_rec',
        'ru': 'eslav_PP-OCRv5_mobile_rec',
        'ar': 'arabic_PP-OCRv5_mobile_rec',
    }


def canvas_jpeg(text: str) -> bytes:
    """Black text on white, as the drawing canvas uploads it."""
    image = Image.new('RGB', (900, 200), 'white')
    ImageDraw.Draw(image).text((40, 60), text, fill='black', font=ImageFont.load_default(size=64))
    out = io.BytesIO()
    image.save(out, format='JPEG')
    return out.getvalue()


def test_reads_a_canvas_into_text_with_confidences() -> None:
    result = ocr.recognize(canvas_jpeg('Jazz quiz vexes'), 'en')
    text = ''.join(t for t, _ in result).replace(' ', '').lower()
    assert text == 'jazzquizvexes'
    assert all(0 <= confidence <= 1 for _, confidence in result)


def test_a_blank_canvas_reads_as_nothing() -> None:
    assert ocr.recognize(canvas_jpeg(''), 'en') == []
