"""Create the Ranex GitHub App from GitHub's own manifest handshake.

The App is still a publisher: this module obtains the identity GitHub will
attribute checks to, stores the PEM outside the repository, and pins
`ranex/acceptance` as a required check from that App. Nothing here evaluates.
"""

from __future__ import annotations

import json
import os
import re
import secrets
import threading
import urllib.parse
from collections.abc import Callable, Mapping
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

from ranex.cli.repository import committable_into
from ranex.foundation.canonical import canonical_json_bytes
from ranex.github_app.client import (
    API_ROOT,
    ClientRefusal,
    complete_repository_rulesets,
    convert_app_manifest,
    create_repository_ruleset,
    list_repository_rulesets,
    split_repository,
)
from ranex.github_app.publisher import CHECK_NAME

MANIFEST_PERMISSIONS = {
    "checks": "write",
    "contents": "read",
    "pull_requests": "read",
}
MANIFEST_EVENTS = ("pull_request",)
IDENTITY_NAME = "identity.json"
KEY_NAME = "app.pem"
SECRET_NAME = "webhook-secret"
RULESET_NAME = "ranex-acceptance"
WEB_ROOT = "https://github.com"
WEB_ROOT_VARIABLE = "RANEX_GITHUB_WEB_ROOT"
_CODE_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


def web_root_from_environment() -> str:
    """github.com, or the operator's Enterprise web origin."""

    return (os.environ.get(WEB_ROOT_VARIABLE) or WEB_ROOT).rstrip("/")


def _require_https_url(value: str, *, what: str) -> str:
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc or parsed.fragment:
        raise ClientRefusal(
            "E-GITHUB-WEBHOOK-NOT-HTTPS" if what == "webhook" else "E-GITHUB-BAD-URL",
            f"{what} must be an https URL without a fragment: {value!r}",
        )
    return value


def app_manifest(
    *,
    name: str,
    homepage: str,
    webhook_url: str,
    redirect_url: str | None = None,
) -> dict[str, Any]:
    """The frozen permission/event set GitHub's create-from-manifest form posts."""

    if not name or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}", name):
        raise ClientRefusal("E-GITHUB-BAD-URL", f"invalid App name: {name!r}")
    _require_https_url(homepage, what="homepage")
    _require_https_url(webhook_url, what="webhook")
    manifest: dict[str, Any] = {
        "name": name,
        "url": homepage,
        "public": False,
        "default_permissions": dict(MANIFEST_PERMISSIONS),
        "default_events": list(MANIFEST_EVENTS),
        "hook_attributes": {"url": webhook_url, "active": True},
    }
    if redirect_url is not None:
        parsed = urllib.parse.urlparse(redirect_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ClientRefusal(
                "E-GITHUB-BAD-URL", f"redirect must be an absolute URL: {redirect_url!r}"
            )
        manifest["redirect_url"] = redirect_url
    return manifest


def manifest_form_html(manifest: Mapping[str, Any], *, state: str, web_root: str) -> str:
    """A one-button form that posts the frozen manifest to GitHub."""

    action = f"{web_root}/settings/apps/new?state={urllib.parse.quote(state, safe='')}"
    payload = json.dumps(dict(manifest), separators=(",", ":"))
    escaped = (
        payload.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")
    )
    return (
        "<!DOCTYPE html><html><body>"
        f'<form action="{action}" method="post">'
        f'<input type="hidden" name="manifest" value="{escaped}">'
        '<input type="submit" value="Create Ranex GitHub App">'
        "</form></body></html>"
    )


def new_manifest_state() -> str:
    return secrets.token_urlsafe(32)


def _refuse_committable(path: Path, repository_root: Path) -> Path:
    resolved = Path(path).expanduser()
    if not resolved.is_absolute():
        raise ClientRefusal(
            "E-GITHUB-KEY-INSIDE-REPO",
            f"credentials directory must be an absolute path, got {path}",
        )
    resolved = resolved.resolve()
    if committable_into(resolved, repository_root):
        raise ClientRefusal(
            "E-GITHUB-KEY-INSIDE-REPO",
            f"{str(path)!r} resolves inside the governed repository",
        )
    return resolved


def _write_exclusive(parent_fd: int, name: str, data: bytes, *, mode: int) -> None:
    handle = os.open(
        name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC, mode, dir_fd=parent_fd
    )
    try:
        os.fchmod(handle, mode)
        view = memoryview(data)
        while view:
            written = os.write(handle, view)
            if written <= 0:
                raise OSError("secret write made no progress")
            view = view[written:]
        os.fsync(handle)
    finally:
        os.close(handle)


def store_credentials(
    directory: Path,
    conversion: Mapping[str, Any],
    *,
    repository_root: Path,
) -> Path:
    """Exclusive-create the PEM, webhook secret and public identity.

    `pem` and `webhook_secret` never leave this function except as file bytes.
    """

    target = _refuse_committable(directory, repository_root)
    try:
        app_id = conversion["id"]
        pem = conversion["pem"]
        secret = conversion["webhook_secret"]
    except KeyError as exc:
        raise ClientRefusal(
            "E-GITHUB-API-REFUSED", f"conversion response lacked {exc}"
        ) from exc
    if type(app_id) is not int or app_id <= 0:
        raise ClientRefusal("E-GITHUB-API-REFUSED", "conversion id is not a positive integer")
    if not isinstance(pem, str) or "BEGIN" not in pem:
        raise ClientRefusal("E-GITHUB-API-REFUSED", "conversion pem is not a PEM private key")
    if not isinstance(secret, str) or not secret:
        raise ClientRefusal("E-GITHUB-API-REFUSED", "conversion webhook_secret is empty")
    slug = conversion.get("slug")
    html_url = conversion.get("html_url")
    identity = {
        "app_id": app_id,
        "slug": slug if isinstance(slug, str) else "",
        "html_url": html_url if isinstance(html_url, str) else "",
    }
    os.makedirs(target, mode=0o700, exist_ok=True)
    parent = os.open(target, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        try:
            stored = Path(os.readlink(f"/proc/self/fd/{parent}")).resolve()
        except OSError as exc:
            raise ClientRefusal(
                "E-GITHUB-KEY-UNREADABLE",
                f"cannot confirm credentials directory {target}: {exc}",
            ) from exc
        if committable_into(stored, repository_root):
            raise ClientRefusal(
                "E-GITHUB-KEY-INSIDE-REPO",
                f"{str(directory)!r} resolves inside the governed repository",
            )
        for name in (KEY_NAME, SECRET_NAME, IDENTITY_NAME):
            if (stored / name).exists():
                raise ClientRefusal(
                    "E-GITHUB-CREDENTIALS-EXIST",
                    f"refusing to overwrite {stored / name}; remove it deliberately",
                )
        key_bytes = pem.encode("ascii")
        if not key_bytes.endswith(b"\n"):
            key_bytes += b"\n"
        secret_bytes = secret.encode("utf-8")
        if not secret_bytes.endswith(b"\n"):
            secret_bytes += b"\n"
        _write_exclusive(parent, KEY_NAME, key_bytes, mode=0o600)
        _write_exclusive(parent, SECRET_NAME, secret_bytes, mode=0o600)
        _write_exclusive(parent, IDENTITY_NAME, canonical_json_bytes(identity), mode=0o600)
        os.fsync(parent)
    finally:
        os.close(parent)
    return stored


def convert_and_store(
    code: str,
    directory: Path,
    *,
    repository_root: Path,
    api_root: str = API_ROOT,
) -> Path:
    """Trade the one-hour manifest code for credentials on disk."""

    if not _CODE_PATTERN.fullmatch(code) or len(code) > 128:
        raise ClientRefusal("E-GITHUB-BAD-MANIFEST-CODE", "malformed conversion code")
    return store_credentials(
        directory, convert_app_manifest(code, api_root=api_root), repository_root=repository_root
    )


def credentials_paths(directory: Path) -> tuple[Path, Path, Path]:
    root = Path(directory)
    return root / KEY_NAME, root / SECRET_NAME, root / IDENTITY_NAME


def load_stored_identity(directory: Path) -> dict[str, Any]:
    _, _, identity_path = credentials_paths(directory)
    try:
        identity = json.loads(identity_path.read_bytes())
    except (OSError, ValueError) as exc:
        raise ClientRefusal("E-GITHUB-CREDENTIALS-ABSENT", f"{identity_path}: {exc}") from exc
    if not isinstance(identity, dict) or type(identity.get("app_id")) is not int:
        raise ClientRefusal("E-GITHUB-CREDENTIALS-ABSENT", f"{identity_path}: missing app_id")
    return identity


class RedirectCapture(HTTPServer):
    """One localhost catcher: the form, then GitHub's `code` query."""

    def __init__(self, bind: tuple[str, int], *, state: str, form_html: str) -> None:
        self.state = state
        self.form_html = form_html.encode("utf-8")
        self.code: str | None = None
        self.error: str | None = None
        super().__init__(bind, _RedirectHandler)


class _RedirectHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self) -> None:  # noqa: N802 — stdlib naming
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path not in {"/", "/redirect"}:
            self._answer(404, b"no such endpoint", "text/plain; charset=utf-8")
            return
        query = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
        if "code" in query:
            state = query.get("state", [""])[0]
            code = query.get("code", [""])[0]
            server = self.server
            assert isinstance(server, RedirectCapture)
            if state != server.state or not _CODE_PATTERN.fullmatch(code):
                server.error = "state-mismatch"
                self._answer(403, b"state mismatch", "text/plain; charset=utf-8")
                threading.Thread(target=server.shutdown, daemon=True).start()
                return
            server.code = code
            self._answer(
                200,
                b"Ranex stored the conversion code. You can close this window.",
                "text/plain; charset=utf-8",
            )
            threading.Thread(target=server.shutdown, daemon=True).start()
            return
        server = self.server
        assert isinstance(server, RedirectCapture)
        self._answer(200, server.form_html, "text/html; charset=utf-8")

    def _answer(self, status: int, payload: bytes, content_type: str) -> None:
        self.close_connection = True
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: Any) -> None:
        return


def serve_manifest_redirect(
    bind: tuple[str, int],
    *,
    state: str,
    form_html: str,
    on_listen: Callable[[RedirectCapture], None] | None = None,
) -> RedirectCapture:
    """Serve the form and capture GitHub's redirect; returns after shutdown."""

    server = RedirectCapture(bind, state=state, form_html=form_html)
    if on_listen is not None:
        on_listen(server)
    try:
        server.serve_forever()
    finally:
        server.server_close()
    return server


def ruleset_body(app_id: int, branch: str) -> dict[str, Any]:
    if not re.fullmatch(r"[A-Za-z0-9._/-]+", branch) or ".." in branch:
        raise ClientRefusal("E-GITHUB-BAD-URL", f"invalid branch name: {branch!r}")
    return {
        "name": RULESET_NAME,
        "target": "branch",
        "enforcement": "active",
        "conditions": {"ref_name": {"include": [f"refs/heads/{branch}"], "exclude": []}},
        "rules": [{
            "type": "required_status_checks",
            "parameters": {
                "strict_required_status_checks_policy": True,
                "required_status_checks": [
                    {"context": CHECK_NAME, "integration_id": app_id},
                ],
            },
        }],
    }


def acceptance_pin(ruleset: Mapping[str, Any]) -> int | None:
    """The integration_id pinning `ranex/acceptance`, if this ruleset names it."""

    rules = ruleset.get("rules")
    if not isinstance(rules, list):
        return None
    for rule in rules:
        if not isinstance(rule, dict) or rule.get("type") != "required_status_checks":
            continue
        parameters = rule.get("parameters")
        if not isinstance(parameters, dict):
            continue
        checks = parameters.get("required_status_checks")
        if not isinstance(checks, list):
            continue
        for check in checks:
            if (
                isinstance(check, dict)
                and check.get("context") == CHECK_NAME
                and type(check.get("integration_id")) is int
            ):
                return check["integration_id"]
    return None


def _strict_acceptance_rule(rule: Any, app_id: int) -> bool:
    if not isinstance(rule, dict) or acceptance_pin({"rules": [rule]}) != app_id:
        return False
    parameters = rule["parameters"]
    return (
        parameters.get("strict_required_status_checks_policy") is True
        and parameters.get("do_not_enforce_on_create", False) is False
    )


def pin_acceptance_ruleset(
    token: str,
    repository: str,
    app_id: int,
    *,
    branch: str,
    api_root: str = API_ROOT,
) -> str:
    """Create the App-pinned ruleset, or confirm one already pins this App.

    A same-named check from another App is a conflict, not a replacement.
    """

    split_repository(repository)
    desired = ruleset_body(app_id, branch)
    summaries = list_repository_rulesets(token, repository, api_root=api_root)
    reusable = False
    for ruleset in complete_repository_rulesets(
        token, repository, summaries, api_root=api_root
    ):
        pinned = acceptance_pin(ruleset)
        if pinned is None:
            continue
        if pinned == app_id:
            # A pin alone proves neither enforcement nor branch coverage.
            # Reuse only the exact scope and strict policy we would create;
            # broader/custom rules remain untouched alongside the new rule.
            if (
                ruleset.get("target") == desired["target"]
                and ruleset.get("enforcement") == "active"
                and ruleset.get("conditions") == desired["conditions"]
                and not ruleset.get("bypass_actors")
                and any(_strict_acceptance_rule(rule, app_id) for rule in ruleset.get("rules", []))
            ):
                reusable = True
            continue
        raise ClientRefusal(
            "E-GITHUB-RULESET-CONFLICT",
            f"{repository} already requires {CHECK_NAME} from integration_id {pinned}",
        )
    if reusable:
        return "existing"
    create_repository_ruleset(
        token, repository, desired, api_root=api_root
    )
    return "created"


