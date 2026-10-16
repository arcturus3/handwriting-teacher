import json
import threading
from typing import Any
from unittest.mock import patch

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


PHONE = analytics.Client(ip='203.0.113.9', user_agent='Mozilla/5.0 (iPhone) Phone/1.0')


def test_an_event_carries_the_browser_that_caused_it_so_it_joins_that_visit() -> None:
    sent: list[dict[str, Any]] = []
    done = threading.Event()
    track = analytics.umami_tracker(
        url='https://analytics.example', website_id='site-1', hostname='betterletters.app',
        send=recording_send(FakeResponse(200, '{}'), sent, done), client=lambda: PHONE,
    )
    track('language-changed', {'language': 'ar'})
    assert done.wait(2)
    payload = sent[0]['body']['payload']
    assert payload['ip'] == '203.0.113.9'
    assert payload['userAgent'] == 'Mozilla/5.0 (iPhone) Phone/1.0'


def test_an_event_no_browser_caused_goes_out_as_beaker_so_the_server_stands_out() -> None:
    sent: list[dict[str, Any]] = []
    done = threading.Event()
    track = analytics.umami_tracker(
        url='https://analytics.example', website_id='site-1', hostname='betterletters.app',
        send=recording_send(FakeResponse(200, '{}'), sent, done), client=lambda: None,
    )
    track('language-changed', {'language': 'ar'})
    assert done.wait(2)
    assert 'ip' not in sent[0]['body']['payload']
    assert 'userAgent' not in sent[0]['body']['payload']
    assert ' BeakerBrowser/' in sent[0]['headers']['User-Agent']


def test_the_browser_is_read_during_the_request_not_when_the_event_is_sent() -> None:
    sent: list[dict[str, Any]] = []
    done = threading.Event()
    current: list[analytics.Client | None] = [PHONE]
    track = analytics.umami_tracker(
        url='https://analytics.example', website_id='site-1', hostname='betterletters.app',
        send=recording_send(FakeResponse(200, '{}'), sent, done), client=lambda: current[0],
    )
    with patch.object(analytics, '_executor') as executor, patch.object(analytics, '_pending', set()):
        track('sentence-generated', {'language': 'en'})
        current[0] = None  # the request is over by the time the event goes out
        deliver, *args = executor.submit.call_args.args
    deliver(*args)
    assert done.wait(2)
    assert sent[0]['body']['payload']['ip'] == '203.0.113.9'


def test_the_browser_is_the_address_nginx_saw_and_the_user_agent() -> None:
    headers = {
        'X-Real-IP': '203.0.113.9',
        'X-Forwarded-For': '198.51.100.7, 203.0.113.9',
        'User-Agent': 'Phone/1.0',
    }
    assert analytics.client_from_headers(headers.get) == analytics.Client(
        ip='203.0.113.9', user_agent='Phone/1.0'
    )
    # Without X-Real-IP, nginx's address is the last X-Forwarded-For entry.
    del headers['X-Real-IP']
    assert analytics.client_from_headers(headers.get).ip == '203.0.113.9'
    assert analytics.client_from_headers({}.get) == analytics.Client()


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
