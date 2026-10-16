import io
import pathlib

from PIL import Image, ImageDraw, ImageFont

import ocr
from align import align

FIXTURES = pathlib.Path(__file__).parent / 'fixtures'


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


def staggered_canvas_jpeg(words: list[str], drops: list[int]) -> bytes:
    """Words left to right, each dropped by its own amount, as handwriting wanders."""
    image = Image.new('RGB', (1400, 400), (220, 220, 220))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=72)
    x = 40
    for word, drop in zip(words, drops):
        draw.text((x, 60 + drop), word, fill='black', font=font)
        x += draw.textlength(word + ' ', font=font)
    out = io.BytesIO()
    image.save(out, format='JPEG')
    return out.getvalue()


def test_words_at_different_heights_come_back_left_to_right() -> None:
    # Later words sit higher, so Paddle's top-to-bottom order would put them first.
    image = staggered_canvas_jpeg(['A', 'cat', 'can', 'relax'], [60, 40, 0, 20])
    text = ' '.join(t for t, _ in ocr.recognize(image, 'en')).lower()
    assert text.split() == ['a', 'cat', 'can', 'relax']


def test_separate_lines_still_read_top_to_bottom() -> None:
    image = Image.new('RGB', (900, 400), 'white')
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=64)
    draw.text((500, 40), 'first', fill='black', font=font)
    draw.text((40, 240), 'second', fill='black', font=font)
    out = io.BytesIO()
    image.save(out, format='JPEG')
    assert [t.lower() for t, _ in ocr.recognize(out.getvalue(), 'en')] == ['first', 'second']


def test_big_writing_on_a_high_density_canvas_keeps_every_letter() -> None:
    # A 1,360 by 300 CSS-pixel canvas at device pixel ratio 2, written edge to edge with a thick pen.
    image = Image.new('RGB', (2720, 600), (220, 220, 220))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=300)
    draw.text((120, 80), 'Steve keeps', fill='black', font=font, stroke_width=6, stroke_fill='black')
    out = io.BytesIO()
    image.save(out, format='JPEG')
    text = ''.join(t for t, _ in ocr.recognize(out.getvalue(), 'en')).replace(' ', '').lower()
    assert text == 'stevekeeps'


def test_large_real_handwriting_is_read() -> None:
    # Femi's "Fred", cropped from his screen: letters about 240 px tall on a 1,344 by 400
    # canvas. At that size the detector found only the "e".
    image = (FIXTURES / 'fred-large-handwriting.jpg').read_bytes()
    reading = ''.join(''.join(t.split()) for t, _ in ocr.recognize(image, 'en'))
    assert sum(align('Fredjumpsforjoy.', reading)[:4]) >= 3, reading
