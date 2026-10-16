# pyright: strict
"""Practice events, sent from the server to Umami so ad blockers can't hide them.

Page views come from Umami's script in the HTML pages; these are the events behind them.
"""
import json
import sys
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from concurrent.futures import Future, ThreadPoolExecutor, wait

EventValue = str | int | float | bool
EventData = Mapping[str, EventValue]
# Records one event; never raises and never waits, so a request can't be held up by it.
Track = Callable[[str, EventData], None]
# Posts a body and returns the status and response text.
Send = Callable[[str, bytes, dict[str, str]], tuple[int, str]]

# The longest event name and text value Umami stores.
MAX_NAME = 50
MAX_TEXT = 500
# Umami drops requests whose User-Agent looks like a bot, which urllib's default does.
USER_AGENT = (
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/140.0.0.0 Safari/537.36'
)
# The page every server event is filed under, apart from the real pages.
EVENT_PATH = '/practice'
DEFAULT_HOSTNAME = 'betterletters.app'
TIMEOUT_SECONDS = 5

_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix='analytics')
_pending: set[Future[None]] = set()


def post(url: str, body: bytes, headers: dict[str, str]) -> tuple[int, str]:
    request = urllib.request.Request(url, data=body, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return response.status, response.read().decode()
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode(errors='replace')


def _trimmed(data: EventData) -> dict[str, EventValue]:
    return {key: value[:MAX_TEXT] if isinstance(value, str) else value for key, value in data.items()}


def umami_tracker(url: str, website_id: str, hostname: str, send: Send = post) -> Track:
    endpoint = url.rstrip('/') + '/api/send'
    headers = {'Content-Type': 'application/json', 'User-Agent': USER_AGENT}

    def deliver(name: str, data: EventData) -> None:
        body = json.dumps({
            'type': 'event',
            'payload': {
                'website': website_id,
                'hostname': hostname,
                'url': EVENT_PATH,
                'name': name[:MAX_NAME],
                'data': _trimmed(data),
            },
        }).encode()
        try:
            status, text = send(endpoint, body, headers)
            if status >= 400:
                raise RuntimeError(f'Umami answered {status}: {text[:200]}')
            # Umami answers a request it takes for a bot with 200 and this, and records nothing.
            if '"beep"' in text:
                raise RuntimeError('Umami took the event for a bot')
        except Exception as error:  # Analytics must never break practice; log and move on.
            print(f'analytics: {name} was not recorded: {error!r}', file=sys.stderr)

    def track(name: str, data: EventData) -> None:
        future = _executor.submit(deliver, name, data)
        _pending.add(future)
        future.add_done_callback(_pending.discard)

    return track


def flush() -> None:
    """Waits for every event sent so far."""
    wait(list(_pending))


def tracker_from_env(env: Mapping[str, str]) -> Track | None:
    """Umami tracking as the environment configures it; off without a URL and website ID."""
    url = env.get('UMAMI_URL', '')
    website_id = env.get('UMAMI_WEBSITE_ID', '')
    if not url or not website_id:
        return None
    return umami_tracker(url, website_id, env.get('ANALYTICS_HOSTNAME', DEFAULT_HOSTNAME))
