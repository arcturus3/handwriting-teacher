"""The writing box on a phone, in a real (headless) browser.

Skipped where Playwright isn't installed, as in the Docker build.
"""
import threading
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any
from unittest.mock import patch

import pytest

sync_api = pytest.importorskip('playwright.sync_api')
from werkzeug.serving import make_server  # noqa: E402

import app  # noqa: E402

if TYPE_CHECKING:
    from playwright.sync_api import Page

PHONE = {'viewport': {'width': 390, 'height': 844}, 'has_touch': True, 'is_mobile': True}
PHONE_SIDEWAYS = {**PHONE, 'viewport': {'width': 844, 'height': 390}}


@pytest.fixture(scope='module')
def site() -> Iterator[str]:
    with patch.object(app, 'generate_samples', return_value=['Jazz quiz']), \
            patch.object(app.ocr, 'recognize', return_value=[('Jazz', 0.9)]):
        server = make_server('127.0.0.1', 0, app.app)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        yield f'http://127.0.0.1:{server.server_port}'
        server.shutdown()


def open_page(site: str, device: dict[str, Any]) -> Iterator['Page']:
    with sync_api.sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_context(**device).new_page()
        page.goto(site)
        page.wait_for_function("document.getElementById('sample').textContent === 'Jazz quiz'")
        yield page
        browser.close()


@pytest.fixture()
def page(site: str) -> Iterator['Page']:
    yield from open_page(site, PHONE)


@pytest.fixture()
def sideways_page(site: str) -> Iterator['Page']:
    yield from open_page(site, PHONE_SIDEWAYS)


def turned(page: 'Page') -> bool:
    """Whether the writing area is drawn sideways, for a phone held upright."""
    return page.evaluate(
        "getComputedStyle(document.getElementById('writingArea')).transform !== 'none'")


def canvas_size(page: 'Page') -> tuple[int, int]:
    """The canvas's own width and height, whichever way it's drawn on screen."""
    return page.evaluate("""() => {
        const c = document.getElementById('defaultCanvas0');
        return [c.offsetWidth, c.offsetHeight];
    }""")


def write(page: 'Page', points: list[tuple[float, float]]) -> None:
    """Draws through points given in the canvas's own coordinates, as the writer sees them."""
    box = canvas_box(page)
    sideways = turned(page)

    def on_screen(x: float, y: float) -> tuple[float, float]:
        if sideways:  # turned a quarter clockwise: the canvas's top runs down the right edge
            return box['x'] + box['width'] - y, box['y'] + x
        return box['x'] + x, box['y'] + y

    page.mouse.move(*on_screen(*points[0]))
    page.mouse.down()
    for point in points[1:]:
        page.mouse.move(*on_screen(*point), steps=4)
    page.mouse.up()


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
    width, height = canvas_size(page)
    write(page, [(40, 40), (width - 40, height - 40)])


def test_full_screen_on_an_upright_phone_turns_the_writing_area_landscape(page: 'Page') -> None:
    assert canvas_box(page)['height'] < 300
    page.get_by_role('button', name='Full screen').tap()

    assert turned(page)
    width, height = canvas_size(page)
    assert width > 750 and width > 2 * height  # the phone's length, less a margin
    assert page.locator('#sample').is_visible()
    assert page.get_by_role('button', name='Submit').is_visible()
    assert page.get_by_role('button', name='Exit full screen').is_visible()


def test_writing_along_the_turned_phone_writes_along_the_line(page: 'Page') -> None:
    page.get_by_role('button', name='Full screen').tap()
    box = canvas_box(page)
    # Held sideways, a line of writing runs down the upright screen.
    page.mouse.move(box['x'] + box['width'] / 2, box['y'] + 60)
    page.mouse.down()
    page.mouse.move(box['x'] + box['width'] / 2, box['y'] + 460, steps=20)
    page.mouse.up()

    left, top, right, bottom = ink_bounds(page)
    assert right - left > 350 and bottom - top < 30


def test_full_screen_on_a_phone_already_sideways_just_fills_it(sideways_page: 'Page') -> None:
    sideways_page.get_by_role('button', name='Full screen').tap()

    assert not turned(sideways_page)
    width, height = canvas_size(sideways_page)
    assert width > 800 and height > 150
    assert sideways_page.locator('#sample').is_visible()
    assert sideways_page.get_by_role('button', name='Submit').is_visible()


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


def ink_bounds(page: 'Page') -> tuple[int, int, int, int]:
    """Left, top, right and bottom of the writing, in canvas pixels."""
    return page.evaluate("""() => {
        const c = document.getElementById('defaultCanvas0');
        const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data;
        let left = c.width, top = c.height, right = -1, bottom = -1;
        for (let y = 0; y < c.height; y++)
            for (let x = 0; x < c.width; x++)
                if (d[(y * c.width + x) * 4] < 100) {
                    left = Math.min(left, x); right = Math.max(right, x);
                    top = Math.min(top, y); bottom = y;
                }
        return [left, top, right, bottom];
    }""")


def ink_height(page: 'Page') -> float:
    """How tall the writing is, in canvas pixels."""
    _, top, _, bottom = ink_bounds(page)
    return max(0, bottom - top + 1)


def test_a_line_written_across_the_top_of_full_screen_stays_big_enough_to_read(
        page: 'Page') -> None:
    page.get_by_role('button', name='Full screen').tap()
    # A zigzag across the top left, like a line of letters.
    write(page, [(30 + i * 30, 40 if i % 2 == 0 else 130) for i in range(11)])
    written = ink_height(page)

    page.get_by_role('button', name='Exit full screen').tap()
    # It fits the small box as written, so it shouldn't shrink with the empty page below it.
    assert ink_height(page) >= 0.9 * written
