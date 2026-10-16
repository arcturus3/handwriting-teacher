import pathlib
import struct

UMAMI_SCRIPT = (
    '<script defer src="https://analytics.davidteju.dev/script.js"'
    ' data-website-id="3ad4ab8f-2cf1-4d54-9480-6a4f2b1227ad"'
    ' data-domains="betterletters.app,www.betterletters.app"></script>'
)

# Favicon services (DuckDuckGo's, which Umami's dashboard uses) skip SVG icons, so every page
# also links a PNG of the same logo.
ICON_LINKS = (
    '<link rel="icon" type="image/svg+xml" href="/static/favicon.svg">',
    '<link rel="icon" type="image/png" sizes="192x192" href="/static/favicon.png">',
    '<link rel="apple-touch-icon" href="/static/favicon.png">',
)
STATIC = pathlib.Path(__file__).parent / 'static'


def pages() -> list[pathlib.Path]:
    found = sorted(STATIC.glob('*.html'))
    assert [page.name for page in found] == ['about.html', 'index.html', 'instructions.html']
    return found


def test_every_page_counts_its_views_on_the_live_site_only() -> None:
    for page in pages():
        assert UMAMI_SCRIPT in page.read_text(), page.name


def test_every_page_links_the_logo_as_svg_and_as_png() -> None:
    for page in pages():
        for link in ICON_LINKS:
            assert link in page.read_text(), f'{page.name}: {link}'
    png = (STATIC / 'favicon.png').read_bytes()
    assert png[1:4] == b'PNG'
    width, height = struct.unpack('>II', png[16:24])
    assert width == height >= 180
