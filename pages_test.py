import pathlib

UMAMI_SCRIPT = (
    '<script defer src="https://analytics.davidteju.dev/script.js"'
    ' data-website-id="3ad4ab8f-2cf1-4d54-9480-6a4f2b1227ad"'
    ' data-domains="betterletters.app,www.betterletters.app"></script>'
)


def test_every_page_counts_its_views_on_the_live_site_only() -> None:
    pages = sorted(pathlib.Path(__file__).parent.joinpath('static').glob('*.html'))
    assert [page.name for page in pages] == ['about.html', 'index.html', 'instructions.html']
    for page in pages:
        assert UMAMI_SCRIPT in page.read_text(), page.name
