import json
import threading
from typing import Any

import analytics


class FakeResponse:
    def __init__(self, status: int, body: str) -> None:
        self.status = status
        self.body = body


def recording_send(
    response: FakeResponse, sent: list[dict[str, Any]], done: threading.Event
) -> analytics.Send:
    def send(url: str, body: bytes, headers: dict[str, str]) -> tuple[int, str]:
        sent.append({'url': url, 'body': json.loads(body), 'headers': headers})
        done.set()
        return response.status, response.body
    return send


def test_posts_an_event_to_umami_as_a_browser() -> None:
    sent: list[dict[str, Any]] = []
    done = threading.Event()
    track = analytics.umami_tracker(
        url='https://analytics.example',
        website_id='site-1',
        hostname='betterletters.app',
        send=recording_send(FakeResponse(200, '{"cache":"x"}'), sent, done),
    )
    track('submission-scored', {'language': 'ru', 'letters': 12})
    assert done.wait(2)
    assert sent[0]['url'] == 'https://analytics.example/api/send'
    assert sent[0]['body'] == {
        'type': 'event',
        'payload': {
            'website': 'site-1',
            'hostname': 'betterletters.app',
            'url': '/practice',
            'name': 'submission-scored',
            'data': {'language': 'ru', 'letters': 12},
        },
    }
    assert 'Mozilla' in sent[0]['headers']['User-Agent']


def test_a_refused_or_bot_flagged_event_is_logged_not_raised(capsys: Any) -> None:
    for response in (FakeResponse(400, 'bad'), FakeResponse(200, '{"beep":"boop"}')):
        done = threading.Event()
        track = analytics.umami_tracker(
            url='https://analytics.example', website_id='site-1', hostname='betterletters.app',
            send=recording_send(response, [], done),
        )
        track('sentence-generated', {'language': 'en'})
        assert done.wait(2)
    analytics.flush()
    assert capsys.readouterr().err.count('analytics: sentence-generated was not recorded') == 2


def test_long_names_and_text_are_cut_to_what_umami_stores() -> None:
    sent: list[dict[str, Any]] = []
    done = threading.Event()
    track = analytics.umami_tracker(
        url='https://analytics.example', website_id='site-1', hostname='betterletters.app',
        send=recording_send(FakeResponse(200, '{}'), sent, done),
    )
    track('n' * 80, {'text': 't' * 900})
    assert done.wait(2)
    assert len(sent[0]['body']['payload']['name']) == 50
    assert len(sent[0]['body']['payload']['data']['text']) == 500


def test_tracking_is_off_without_a_website_id() -> None:
    assert analytics.tracker_from_env({'UMAMI_URL': 'https://analytics.example'}) is None
    assert analytics.tracker_from_env({'UMAMI_WEBSITE_ID': 'site-1'}) is None
    assert analytics.tracker_from_env(
        {'UMAMI_URL': 'https://analytics.example', 'UMAMI_WEBSITE_ID': 'site-1'}
    ) is not None
