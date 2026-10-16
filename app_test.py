import io
from typing import Any
from unittest.mock import patch

import analytics
import app


def recorded_events() -> tuple[list[tuple[str, dict[str, Any]]], Any]:
    events: list[tuple[str, dict[str, Any]]] = []
    return events, patch.object(app, 'track', lambda name, data: events.append((name, dict(data))))


def test_practice_records_language_sentence_and_score_without_any_writing() -> None:
    events, tracking = recorded_events()
    client = app.app.test_client()
    with tracking, \
            patch.object(app, 'generate_samples', return_value=['Да он']), \
            patch.object(app.ocr, 'recognize', return_value=[('Да', 0.9)]):
        client.post('/language', json={'language': 'ru'})
        client.get('/sample')
        client.post('/submit_canvas', data={'imageFile': (io.BytesIO(b'jpeg'), 'c.jpg')})

    names = [name for name, _ in events]
    assert names == ['language-changed', 'sentence-generated', 'submission-scored']
    assert events[0][1] == {'language': 'ru'}
    assert events[1][1]['language'] == 'ru'
    scored = events[2][1]
    assert scored['language'] == 'ru'
    assert scored['letters'] == 4
    assert scored['matched'] == 2
    assert scored['read_anything'] is True
    assert isinstance(scored['ocr_ms'], int)
    # Nothing the learner wrote or was asked to write leaves the server.
    assert 'Да' not in repr(events)


def test_a_failed_sentence_is_recorded_before_the_error_surfaces() -> None:
    events, tracking = recorded_events()
    client = app.app.test_client()
    with tracking, patch.object(app, 'generate_samples', side_effect=RuntimeError('down')):
        response = client.get('/sample')
    assert response.status_code == 500
    assert events == [('sentence-failed', {'language': 'en', 'error': 'RuntimeError'})]


def test_events_are_filed_under_the_browser_whose_request_caused_them() -> None:
    headers = {'X-Real-IP': '203.0.113.9', 'User-Agent': 'Phone/1.0'}
    with app.app.test_request_context(headers=headers):
        assert app.requesting_browser() == analytics.Client(ip='203.0.113.9', user_agent='Phone/1.0')
    assert app.requesting_browser() is None
