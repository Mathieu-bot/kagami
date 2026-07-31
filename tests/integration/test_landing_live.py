"""Integration tests against the deployed landing page (live site).

These hit the production host and verify that:

- the root URL serves the static app launcher (HTTP 200, not a redirect);
- the landing page lists the AQI app and the coming-soon apps;
- the AQI app is reachable and its health endpoint reports ``ok``;
- the Google OAuth callback arriving at the root is forwarded to /aqi/.

The module only self-skips when the whole site is unreachable. Once the
host answers, the assertions are strict: a root that does not serve the
landing page (redirect, 403, 404, …) fails the suite, which is exactly
the regression the tests are meant to catch::

    python3 -m pytest tests/integration/test_landing_live.py -v

Override the target with KAGAMI_BASE_URL (staging / local Caddy runs).
"""

import os
import re
import urllib.error
import urllib.request

import pytest

pytestmark = [pytest.mark.integration]

BASE = os.environ.get("KAGAMI_BASE_URL", "https://kagami.tafita.online").rstrip("/")


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


def _body(url, follow=True, timeout=15):
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


def test_root_serves_landing_page():
    status, body = _body(BASE + "/", follow=False)
    assert status == 200, f"root returned HTTP {status} (landing page not served)"
    assert "Company of dashboards" in body
    assert re.search(r'href="/aqi/"', body)


def test_landing_lists_aqi_and_coming_soon_apps():
    status, body = _body(BASE + "/", follow=False)
    assert status == 200, f"root returned HTTP {status}"
    assert "Qualité de l'air" in body
    assert "Santé" in body
    assert "Stations" in body
    assert body.count("Bientôt") >= 2


def test_aqi_app_is_reachable():
    # Streamlit's initial HTML is a JS shell (content renders client-side),
    # so we assert on the shell marker + status; the health test below
    # verifies the backend is actually up.
    status, body = _body(BASE + "/aqi/", timeout=25)
    assert status == 200, f"/aqi/ returned HTTP {status}"
    assert '<div id="root">' in body or "window.prerenderReady" in body


def test_aqi_health_endpoint_is_ok():
    status, body = _body(BASE + "/aqi/_stcore/health", timeout=15)
    assert status == 200, f"health endpoint returned HTTP {status}"
    assert body.strip() == "ok"


def test_oauth_callback_is_forwarded_to_app():
    status, location = _status_and_location(BASE + "/?oauth=callback")
    assert status in (301, 302, 303, 307, 308), f"expected a redirect, got HTTP {status}"
    assert "/aqi/" in location, f"callback not forwarded to the app: {location!r}"
    assert "oauth=callback" in location, f"callback query lost: {location!r}"
