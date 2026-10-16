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
from dataclasses import dataclass

EventValue = str | int | float | bool
EventData = Mapping[str, EventValue]
# Records one event; never raises and never waits, so a request can't be held up by it.
Track = Callable[[str, EventData], None]
# Posts a body and returns the status and response text.
Send = Callable[[str, bytes, dict[str, str]], tuple[int, str]]

# The longest event name and text value Umami stores.
MAX_NAME = 50
MAX_TEXT = 500
# The browser an event no browser caused is filed under. Umami drops requests whose User-Agent
# looks like a bot, which urllib's default does, so this is a real browser's, and one nobody uses,
# so the server stands out in the dashboard as Beaker.
USER_AGENT = (
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
    'BeakerBrowser/1.1.0 Chrome/140.0.0.0 Safari/537.36'
)
# The page every server event is filed under, apart from the real pages.
EVENT_PATH = '/practice'
DEFAULT_HOSTNAME = 'betterletters.app'
TIMEOUT_SECONDS = 5



@dataclass(frozen=True)
class Client:
    """The browser behind an event.

    Umami counts a visitor by address and User-Agent, so an event sent with the ones a browser's
    page views came with lands in that browser's visit.
    """
    ip: str | None = None
    user_agent: str | None = None


def client_from_headers(header: Callable[[str], str | None]) -> Client:
    """The browser a request came from, read through a header getter.

    nginx passes the address it saw as X-Real-IP, which is what Umami records for the same
    browser's page views; it also appends it to X-Forwarded-For, the fallback.
    """
    forwarded = (header('X-Forwarded-For') or '').split(',')[-1].strip()
    return Client(
        ip=header('X-Real-IP') or forwarded or None,
        user_agent=header('User-Agent') or None,
    )


def _no_client() -> Client | None:
    return None


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


def umami_tracker(
    url: str,
    website_id: str,
    hostname: str,
    send: Send = post,
    client: Callable[[], Client | None] = _no_client,
) -> Track:
    """Sends events to Umami; `client` names the browser behind the event being recorded."""
    endpoint = url.rstrip('/') + '/api/send'
    headers = {'Content-Type': 'application/json', 'User-Agent': USER_AGENT}

    def deliver(name: str, data: EventData, browser: Client | None) -> None:
        payload: dict[str, object] = {
            'website': website_id,
            'hostname': hostname,
            'url': EVENT_PATH,
            'name': name[:MAX_NAME],
            'data': _trimmed(data),
        }
        if browser is not None and browser.ip:
            payload['ip'] = browser.ip
        if browser is not None and browser.user_agent:
            payload['userAgent'] = browser.user_agent
        body = json.dumps({'type': 'event', 'payload': payload}).encode()
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
        # Read now: the request the browser comes from is gone by the time the event is sent.
        future = _executor.submit(deliver, name, data, client())
        _pending.add(future)
        future.add_done_callback(_pending.discard)

    return track


def flush() -> None:
    """Waits for every event sent so far."""
    wait(list(_pending))


def tracker_from_env(
    env: Mapping[str, str], client: Callable[[], Client | None] = _no_client
) -> Track | None:
    """Umami tracking as the environment configures it; off without a URL and website ID."""
    url = env.get('UMAMI_URL', '')
    website_id = env.get('UMAMI_WEBSITE_ID', '')
    if not url or not website_id:
        return None
    return umami_tracker(
        url, website_id, env.get('ANALYTICS_HOSTNAME', DEFAULT_HOSTNAME), client=client
    )
