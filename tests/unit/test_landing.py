"""Tests for the landing page artifact and its Caddy routing.

Fast, offline checks on the exact files shipped to the VM: the static
app launcher (www/index.html) and the Caddyfile that serves it at the
root while preserving the AQI app and the Google OAuth callback.

The live HTTP behaviour of the deployed site is covered separately in
tests/integration/test_landing_live.py.
"""

import os
import re
from html.parser import HTMLParser

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
INDEX = os.path.join(ROOT, "www", "index.html")
CADDYFILE = os.path.join(ROOT, "Caddyfile")

# HTML elements that never need a closing tag.
_VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
         "link", "meta", "param", "source", "track", "wbr"}


class _BalanceParser(HTMLParser):
    """Track start/end tags and report imbalances."""

    def __init__(self):
        super().__init__()
        self.stack = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        if tag not in _VOID:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        pass  # self-closing like <svg/> or <circle/>

    def handle_endtag(self, tag):
        if tag in _VOID:
            return
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        else:
            self.errors.append(f"mismatched </{tag}> (stack top: {self.stack[-1:]})")


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


# ─── Landing page (www/index.html) ───


def test_index_exists_and_is_not_empty():
    assert os.path.exists(INDEX), "www/index.html is missing"
    assert len(_read(INDEX).strip()) > 0


def test_index_is_well_formed_html():
    parser = _BalanceParser()
    parser.feed(_read(INDEX))
    parser.close()
    assert not parser.errors, parser.errors
    assert not parser.stack, f"unclosed tags: {parser.stack}"


def test_index_has_brand_and_title():
    html = _read(INDEX)
    assert "<title>Kagami" in html
    assert "<h1>Kagami</h1>" in html
    assert "Company of dashboards" in html


def test_aqi_card_links_to_app():
    html = _read(INDEX)
    assert re.search(r'<a class="card live" href="/aqi/">', html)
    assert "Qualité de l'air" in html
    assert "En ligne" in html


def test_coming_soon_apps_are_listed():
    html = _read(INDEX)
    assert "Santé" in html
    assert "Stations" in html
    assert html.count("Bientôt") >= 2


def test_footer_is_generic_without_login_hint():
    html = _read(INDEX)
    footer = html.split("<footer>")[-1].split("</footer>")[0]
    assert "Company of dashboards" in footer
    assert "/aqi/" not in footer
    assert "login" not in footer.lower()
    assert "connexion" not in footer.lower()


# ─── Caddy routing ───


def test_caddy_serves_landing_at_root():
    caddy = _read(CADDYFILE)
    assert "handle / {" in caddy
    assert "root * /var/www/kagami" in caddy
    assert "file_server" in caddy


def test_caddy_forwards_oauth_callback_to_app():
    caddy = _read(CADDYFILE)
    # The matcher is scoped to the root path: a callback already inside the
    # app (/aqi/?oauth=callback) must NOT match, or Caddy would redirect it
    # to itself in an infinite loop (breaks Google sign-in).
    assert "@oauth {" in caddy
    assert "path /" in caddy
    assert "query oauth=callback" in caddy
    assert "redir @oauth /aqi/?{query} 302" in caddy


def test_caddy_still_proxies_aqi_app():
    caddy = _read(CADDYFILE)
    assert "handle /aqi/* {" in caddy
    assert "reverse_proxy localhost:8501" in caddy
    assert "redir /aqi /aqi/ 308" in caddy


def test_caddy_old_direct_root_redirect_removed():
    caddy = _read(CADDYFILE)
    assert "@root" not in caddy
    assert "redir @root" not in caddy


def test_caddy_oauth_matcher_is_scoped_to_root():
    # Regression guard: an unscoped "@oauth query oauth=callback" would also
    # match /aqi/?oauth=callback, and Caddy would re-redirect the app's own
    # callback to itself forever — breaking Google sign-in.
    caddy = _read(CADDYFILE)
    oauth_block = caddy.split("@oauth")[1].split("}")[0]
    assert "path /" in oauth_block, (
        "OAuth matcher must be scoped to the root path, "
        "otherwise /aqi/?oauth=callback loops forever"
    )
    # The bare inline form ("@oauth query ...") must not be used.
    assert "@oauth query oauth=callback" not in caddy


def test_caddy_root_points_at_deploy_dir():
    # The Caddyfile serves the static landing page from /var/www/kagami.
    # The CD workflow copies www/ there (the git checkout under /home/ubuntu
    # is not readable by the caddy user).
    caddy = _read(CADDYFILE)
    assert "/var/www/kagami" in caddy
    assert "/home/ubuntu/kagami/www" not in caddy
    assert os.path.exists(INDEX)
