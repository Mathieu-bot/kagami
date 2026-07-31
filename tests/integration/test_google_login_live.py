"""Integration tests for the Google OAuth login flow (live site).

When a user clicks "Sign in with Google" the browser eventually lands back
on the ROOT URL (the redirect_uri registered with Google is
``https://kagami.tafita.online/?oauth=callback``). Caddy must forward that
callback to the Streamlit app at /aqi/ **while preserving the code and
state parameters**, otherwise the token exchange fails:

    ?oauth=callback&code=...&state=...  →  302  /aqi/?oauth=callback&code=...&state=...

These tests verify that end-to-end through the deployed Caddy:

- the bare callback is forwarded to the app (regression guard);
- a realistic callback with code + state keeps both parameters;
- the full callback follows the redirect chain and the app answers.

The module self-skips only when the whole site is unreachable; once the
host answers, assertions are strict.

    python3 -m pytest tests/integration/test_google_login_live.py -v
"""

import os
import urllib.error
import urllib.parse
import urllib.request

import pytest

pytestmark = [pytest.mark.integration]

BASE = os.environ.get("KAGAMI_BASE_URL", "https://kagami.tafita.online").rstrip("/")

# A realistic Google callback (values are opaque to Caddy, so any strings
# work here — we just verify they survive the redirect untouched).
CODE = "4/0AX4XfWihPIQGTnM1j3KqzvY9Nfp7vRkXoH7FakeTokenForTesting"
STATE = "oXpR8kQ3vLmN2fBzWqYcFakeStateForTesting"


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Let urlopen return 3xx responses instead of following them."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _open(url, follow=True, timeout=15):
    if follow:
        return urllib.request.urlopen(url, timeout=timeout)
    opener = urllib.request.build_opener(_NoRedirect)
    return opener.open(url, timeout=timeout)


def _status_and_location(url, timeout=15):
    """Return (status, Location) even for 4xx/5xx (which urllib raises)."""
    try:
        with _open(url, follow=False, timeout=timeout) as resp:
            return resp.status, resp.headers.get("Location", "")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers.get("Location", "")


def _body(url, follow=True, timeout=20):
    """Return (status, body) even for 4xx/5xx (which urllib raises)."""
    try:
        with _open(url, follow=follow, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")


@pytest.fixture(scope="module", autouse=True)
def _skip_when_site_unreachable():
    """Skip the whole module only when the host is completely unreachable."""
    try:
        with _open(BASE + "/aqi/_stcore/health", timeout=10):
            pass
    except Exception as exc:
        pytest.skip(f"{BASE} is unreachable ({exc}) — deploy first (see CD)")


def _location_query(location):
    """Parse the query string of a redirect Location back into a dict."""
    _, _, query = location.partition("?")
    return dict(urllib.parse.parse_qsl(query))


def test_oauth_callback_is_forwarded_to_app():
    status, location = _status_and_location(BASE + "/?oauth=callback")
    assert status in (301, 302, 303, 307, 308), f"expected a redirect, got HTTP {status}"
    assert location.startswith("/aqi/"), f"callback not forwarded to the app: {location!r}"
    assert "oauth=callback" in location, f"callback query lost: {location!r}"


def test_google_callback_preserves_code_and_state():
    # Caddy must forward the full query string; dropping code or state would
    # break the OAuth token exchange with Google.
    url = BASE + "/?oauth=callback&code=" + urllib.parse.quote(CODE, safe="") \
        + "&state=" + urllib.parse.quote(STATE, safe="")
    status, location = _status_and_location(url)
    assert status in (301, 302, 303, 307, 308), f"expected a redirect, got HTTP {status}"
    assert location.startswith("/aqi/"), f"callback not forwarded to the app: {location!r}"

    query = _location_query(location)
    assert query.get("oauth") == "callback", f"oauth param lost: {query}"
    assert query.get("code") == CODE, f"code param not preserved: {query.get('code')!r}"
    assert query.get("state") == STATE, f"state param not preserved: {query.get('state')!r}"


def test_google_callback_chain_reaches_app():
    # Follow the 302 with a browser-like request (auto-redirect): the final
    # response must come from the Streamlit app (HTTP 200 shell page).
    status, body = _body(BASE + "/?oauth=callback&code=" + urllib.parse.quote(CODE, safe="")
                         + "&state=" + urllib.parse.quote(STATE, safe=""), follow=True)
    assert status == 200, f"callback chain did not reach the app (HTTP {status})"
    assert '<div id="root">' in body or "window.prerenderReady" in body
