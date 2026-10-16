"""The writing box on a phone, in a real (headless) browser.

Skipped where Playwright isn't installed, as in the Docker build.
"""
import threading
from collections.abc import Iterator
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

sync_api = pytest.importorskip('playwright.sync_api')
from werkzeug.serving import make_server  # noqa: E402

import app  # noqa: E402

if TYPE_CHECKING:
    from playwright.sync_api import Page

PHONE = {'viewport': {'width': 390, 'height': 844}, 'has_touch': True, 'is_mobile': True}


@pytest.fixture(scope='module')
def site() -> Iterator[str]:
    with patch.object(app, 'generate_samples', return_value=['Jazz quiz']), \
            patch.object(app.ocr, 'recognize', return_value=[('Jazz', 0.9)]):
        server = make_server('127.0.0.1', 0, app.app)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        yield f'http://127.0.0.1:{server.server_port}'
        server.shutdown()


@pytest.fixture()
def page(site: str) -> Iterator['Page']:
    with sync_api.sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_context(**PHONE).new_page()
        page.goto(site)
        page.wait_for_function("document.getElementById('sample').textContent === 'Jazz quiz'")
        yield page
        browser.close()


def canvas_box(page: 'Page') -> dict[str, float]:
    box = page.locator('#defaultCanvas0').bounding_box()
    assert box is not None
    return box


def inked_pixels(page: 'Page') -> int:
    return page.evaluate("""() => {
        const c = document.getElementById('defaultCanvas0');
        const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data;
        let n = 0;
        for (let i = 0; i < d.length; i += 4) if (d[i] < 100) n++;
        return n;
    }""")


def scribble(page: 'Page') -> None:
    box = canvas_box(page)
    page.mouse.move(box['x'] + 40, box['y'] + 40)
    page.mouse.down()
    page.mouse.move(box['x'] + box['width'] - 40, box['y'] + box['height'] - 40, steps=20)
    page.mouse.up()


def test_the_writing_box_fills_the_phone_with_the_sentence_and_submit_still_in_view(
        page: 'Page') -> None:
    assert canvas_box(page)['height'] < 300
    page.get_by_role('button', name='Full screen').tap()

    box = canvas_box(page)
    assert box['width'] >= 350 and box['height'] > 600  # all but a 12px margin
    assert page.locator('#sample').is_visible()
    assert page.get_by_role('button', name='Submit').is_visible()
    assert page.get_by_role('button', name='Exit full screen').is_visible()


def test_writing_survives_leaving_full_screen(page: 'Page') -> None:
    page.get_by_role('button', name='Full screen').tap()
    scribble(page)
    drawn = inked_pixels(page)
    assert drawn > 0

    page.get_by_role('button', name='Exit full screen').tap()
    assert canvas_box(page)['height'] < 300
    # Shrunk to fit the small box, so the whole stroke is still there to be read.
    assert inked_pixels(page) > 0
    ink_at_bottom_edge = page.evaluate("""() => {
        const c = document.getElementById('defaultCanvas0');
        const d = c.getContext('2d').getImageData(0, c.height - 4, c.width, 4).data;
        let n = 0;
        for (let i = 0; i < d.length; i += 4) if (d[i] < 100) n++;
        return n;
    }""")
    assert ink_at_bottom_edge == 0, 'the stroke should be scaled into the box, not cut off'


def ink_height(page: 'Page') -> float:
    """How tall the writing is, in canvas pixels."""
    return page.evaluate("""() => {
        const c = document.getElementById('defaultCanvas0');
        const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data;
        let top = c.height, bottom = -1;
        for (let y = 0; y < c.height; y++)
            for (let x = 0; x < c.width; x++)
                if (d[(y * c.width + x) * 4] < 100) { top = Math.min(top, y); bottom = y; }
        return bottom < 0 ? 0 : bottom - top + 1;
    }""")


def test_a_line_written_across_the_top_of_full_screen_stays_big_enough_to_read(
        page: 'Page') -> None:
    page.get_by_role('button', name='Full screen').tap()
    box = canvas_box(page)
    page.mouse.move(box['x'] + 30, box['y'] + 40)
    page.mouse.down()
    for i in range(1, 11):  # a zigzag across the top fifth, like a line of letters
        page.mouse.move(box['x'] + 30 + i * 30, box['y'] + (40 if i % 2 == 0 else 130), steps=4)
    page.mouse.up()
    written = ink_height(page)

    page.get_by_role('button', name='Exit full screen').tap()
    # It fits the small box as written, so it shouldn't shrink with the empty page below it.
    assert ink_height(page) >= 0.9 * written
