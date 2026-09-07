"""The GitHub App client: the only module that speaks to api.github.com.

Transport is stdlib `urllib.request` over TLS and the JWT is minted with the
already-pinned `cryptography` primitive — RS256 per GitHub's server-to-server
contract, issuer-side only, because GitHub verifies the token and this code
never does (ADR-050). Credentials live in the operator's environment and on
disk outside the repository, exactly like every other Ranex key.
"""

from __future__ import annotations

import base64
import json
import os
import stat
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

API_ROOT = "https://api.github.com"
# The pinned API version of the docs this client was written against
# (docs.github.com/rest, verified at this slice's landing). Bumped
# deliberately, never silently.
API_VERSION = "2026-03-10"
MEDIA_TYPE = "application/vnd.github+json"
API_ROOT_VARIABLE = "RANEX_GITHUB_API_ROOT"

APP_ID_VARIABLE = "RANEX_GITHUB_APP_ID"
APP_KEY_VARIABLE = "RANEX_GITHUB_APP_PRIVATE_KEY"
WEBHOOK_SECRET_VARIABLE = "RANEX_GITHUB_WEBHOOK_SECRET"
OPERATOR_TOKEN_VARIABLE = "RANEX_GITHUB_OPERATOR_TOKEN"
OPERATOR_TOKEN_FALLBACK = "GITHUB_TOKEN"

# GitHub rejects an `exp` more than ten minutes ahead; the documented examples
# use iat = now − 60 (clock drift) and exp = now + 600.
_IAT_DRIFT_SECONDS = 60
_EXP_SECONDS = 600
# Refresh a token this far ahead of its expiry, per the documented ~1h life.
_TOKEN_REFRESH_MARGIN = 60


class ClientRefusal(ValueError):
    """The API refused, or the credentials would not stand up."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code} {detail}")
        self.code = code
        self.detail = detail


def split_repository(repository: str) -> tuple[str, str]:
    """`owner/name`, or a named refusal."""

    owner, separator, name = repository.partition("/")
    if not owner or not separator or not name or "/" in name:
        raise ClientRefusal("E-GITHUB-BAD-REPO", f"expected owner/name: {repository!r}")
    return owner, name


def _api_headers(*, token: str | None = None, body: bool = False) -> dict[str, str]:
    headers = {"Accept": MEDIA_TYPE, "X-GitHub-Api-Version": API_VERSION}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    if body:
        headers["Content-Type"] = MEDIA_TYPE
    return headers


def _api_request(
    method: str,
    url: str,
    *,
    token: str | None = None,
    body: Any = None,
    timeout_seconds: float = 30.0,
) -> Any:
    payload = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        method=method,
        headers=_api_headers(token=token, body=payload is not None),
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read()[:200].decode("utf-8", "replace").strip()
        raise ClientRefusal(
            "E-GITHUB-API-REFUSED", f"{method} {url}: HTTP {exc.code} {detail}"
        ) from exc
    except (urllib.error.URLError, OSError) as exc:
        raise ClientRefusal("E-GITHUB-API-REFUSED", f"{method} {url}: {exc}") from exc
    return json.loads(raw) if raw else {}


def convert_app_manifest(code: str, *, api_root: str = API_ROOT) -> dict[str, Any]:
    """Trade GitHub's one-hour manifest `code` for App id, PEM and webhook secret.

    Anonymous: GitHub already proved the operator via the form POST. The
    response carries secrets; callers store them, they never print them.
    """

    response = _api_request(
        "POST", f"{api_root.rstrip('/')}/app-manifests/{code}/conversions"
    )
    if not isinstance(response, dict):
        raise ClientRefusal("E-GITHUB-API-REFUSED", "conversion response was not an object")
    return response


def operator_token_from_environment() -> str:
    """The user token that authors a ruleset. The App JWT cannot."""

    token = os.environ.get(OPERATOR_TOKEN_VARIABLE) or os.environ.get(OPERATOR_TOKEN_FALLBACK)
    if not token:
        raise ClientRefusal(
            "E-GITHUB-OPERATOR-TOKEN-ABSENT",
            f"unset: {OPERATOR_TOKEN_VARIABLE} (or {OPERATOR_TOKEN_FALLBACK})",
        )
    return token


def list_repository_rulesets(
    token: str, repository: str, *, api_root: str = API_ROOT
) -> list[dict[str, Any]]:
    owner, name = split_repository(repository)
    response = _api_request(
        "GET",
        f"{api_root.rstrip('/')}/repos/{owner}/{name}/rulesets",
        token=token,
    )
    if not isinstance(response, list) or not all(isinstance(item, dict) for item in response):
        raise ClientRefusal("E-GITHUB-API-REFUSED", "rulesets listing was not a list of objects")
    return response


def create_repository_ruleset(
    token: str,
    repository: str,
    body: dict[str, Any],
    *,
    api_root: str = API_ROOT,
) -> dict[str, Any]:
    owner, name = split_repository(repository)
    response = _api_request(
        "POST",
        f"{api_root.rstrip('/')}/repos/{owner}/{name}/rulesets",
        token=token,
        body=body,
    )
    if not isinstance(response, dict):
        raise ClientRefusal("E-GITHUB-API-REFUSED", "ruleset create response was not an object")
    return response


def get_repository_ruleset(
    token: str, repository: str, ruleset_id: int, *, api_root: str = API_ROOT
) -> dict[str, Any]:
    owner, name = split_repository(repository)
    response = _api_request(
        "GET",
        f"{api_root.rstrip('/')}/repos/{owner}/{name}/rulesets/{ruleset_id}",
        token=token,
    )
    if not isinstance(response, dict):
        raise ClientRefusal("E-GITHUB-API-REFUSED", "ruleset get response was not an object")
    return response


def complete_repository_rulesets(
    token: str, repository: str, summaries: list[dict[str, Any]], *, api_root: str = API_ROOT
) -> list[dict[str, Any]]:
    """List payloads often omit `rules`; fetch each id so the pin can be read."""

    completed: list[dict[str, Any]] = []
    for summary in summaries:
        if isinstance(summary.get("rules"), list):
            completed.append(summary)
            continue
        ruleset_id = summary.get("id")
        if type(ruleset_id) is not int:
            completed.append(summary)
            continue
        completed.append(
            get_repository_ruleset(token, repository, ruleset_id, api_root=api_root)
        )
    return completed


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


@dataclass(frozen=True, slots=True)
class AppCredentials:
    """Who the App is, from the environment — never from the repository."""

    app_id: str
    private_key_path: Path
    webhook_secret: str

    @classmethod
    def from_environment(cls, repository_root: Path) -> AppCredentials:
        app_id = os.environ.get(APP_ID_VARIABLE)
        key_path = os.environ.get(APP_KEY_VARIABLE)
        secret = os.environ.get(WEBHOOK_SECRET_VARIABLE)
        # The check both refuses loudly and narrows: past it, all three are
        # non-empty strings, which is what the type checker cannot know
        # about `os.environ.get` results on its own.
        if not app_id or not key_path or not secret:
            missing = [
                name
                for name, value in (
                    (APP_ID_VARIABLE, app_id),
                    (APP_KEY_VARIABLE, key_path),
                    (WEBHOOK_SECRET_VARIABLE, secret),
                )
                if not value
            ]
            raise ClientRefusal(
                "E-GITHUB-CREDENTIALS-ABSENT", f"unset: {', '.join(missing)}"
            )
        resolved = Path(key_path).expanduser().resolve()
        root = Path(repository_root).resolve()
        if resolved == root or root in resolved.parents:
            raise ClientRefusal(
                "E-GITHUB-KEY-INSIDE-REPO",
                f"{key_path!r} resolves inside the governed repository",
            )
        return cls(app_id=app_id, private_key_path=resolved, webhook_secret=secret)


def load_private_key(path: Path):
    """Parse the App's PEM key, refusing anything unreadable or exposed.

    The key is the App's identity. A regular file that group or others can
    read is refused before a byte of it is parsed: mode bits are the one
    exposure the loader can see, so it insists on them (0600 or tighter).
    """

    try:
        status = os.stat(path)
    except OSError as exc:
        raise ClientRefusal("E-GITHUB-KEY-UNREADABLE", f"{path}: {exc}") from exc
    if not stat.S_ISREG(status.st_mode):
        raise ClientRefusal("E-GITHUB-KEY-UNREADABLE", f"{path}: not a regular file")
    if status.st_mode & 0o077:
        raise ClientRefusal(
            "E-GITHUB-KEY-EXPOSED",
            f"{path}: mode {oct(status.st_mode & 0o777)} is readable beyond its owner",
        )
    try:
        key_bytes = Path(path).read_bytes()
        return serialization.load_pem_private_key(key_bytes, password=None)
    except (OSError, ValueError, TypeError) as exc:
        raise ClientRefusal("E-GITHUB-KEY-UNREADABLE", f"{path}: {exc}") from exc


def mint_app_jwt(credentials: AppCredentials, *, now: float | None = None) -> str:
    """An RS256 JWT with the documented claims window; GitHub verifies it."""

    current = time.time() if now is None else now
    issued = int(current) - _IAT_DRIFT_SECONDS
    expires = int(current) + _EXP_SECONDS
    # Compact JSON as JWT framing expects; GitHub parses the token, nothing
    # digests it, so canonicalisation plays no part here.
    header = _b64url(
        json.dumps({"alg": "RS256", "typ": "JWT"}, separators=(",", ":")).encode()
    )
    claims = _b64url(
        json.dumps(
            {"exp": expires, "iat": issued, "iss": credentials.app_id},
            separators=(",", ":"),
        ).encode()
    )
    signing_input = f"{header}.{claims}".encode("ascii")
    signature = load_private_key(credentials.private_key_path).sign(
        signing_input, padding.PKCS1v15(), hashes.SHA256()
    )
    return f"{header}.{claims}.{_b64url(signature)}"


@dataclass(frozen=True, slots=True)
class _Token:
    value: str
    expires_at: float


class GitHubClient:
    """A bounded API surface: mint, exchange, publish. Nothing retries."""

    def __init__(
        self,
        credentials: AppCredentials,
        *,
        api_root: str = API_ROOT,
        now: Callable[[], float] = time.time,
        timeout_seconds: float = 30.0,
    ) -> None:
        self._credentials = credentials
        self._api_root = api_root.rstrip("/")
        self._now = now
        self._timeout = timeout_seconds
        self._tokens: dict[int, _Token] = {}

    @property
    def credentials(self) -> AppCredentials:
        """Read-only: the receiver reads the webhook secret from here."""

        return self._credentials

    def _request(self, method: str, path: str, *, token: str, body: Any = None):
        return _api_request(
            method,
            f"{self._api_root}{path}",
            token=token,
            body=body,
            timeout_seconds=self._timeout,
        )

    def installation_token(self, installation_id: int) -> str:
        cached = self._tokens.get(installation_id)
        if cached is not None and cached.expires_at - _TOKEN_REFRESH_MARGIN > self._now():
            return cached.value
        response = self._request(
            "POST",
            f"/app/installations/{installation_id}/access_tokens",
            token=mint_app_jwt(self._credentials, now=self._now()),
        )
        try:
            expires = datetime.fromisoformat(
                str(response["expires_at"]).replace("Z", "+00:00")
            ).timestamp()
            token = _Token(value=str(response["token"]), expires_at=expires)
        except (KeyError, AttributeError, ValueError, TypeError) as exc:
            raise ClientRefusal(
                "E-GITHUB-API-REFUSED",
                f"installation token response lacked token/expires_at: {exc}",
            ) from exc
        self._tokens[installation_id] = token
        return token.value

    def create_check_run(
        self, installation_id: int, repository: str, body: dict[str, Any]
    ) -> dict[str, Any]:
        owner, name = split_repository(repository)
        return self._request(
            "POST",
            f"/repos/{owner}/{name}/check-runs",
            token=self.installation_token(installation_id),
            body=body,
        )

    def list_check_runs(
        self, installation_id: int, repository: str, head_sha: str, *, check_name: str
    ) -> list[dict[str, Any]]:
        """This App's check runs of one name on one commit, for reconciliation.

        GitHub filters by `check_name` and `app_id`; the caller matches the
        `external_id` it stamped at publication. Nothing here decides.
        """

        owner, name = split_repository(repository)
        query = urllib.parse.urlencode(
            {"check_name": check_name, "app_id": self._credentials.app_id, "per_page": 100}
        )
        response = self._request(
            "GET",
            f"/repos/{owner}/{name}/commits/{head_sha}/check-runs?{query}",
            token=self.installation_token(installation_id),
        )
        runs = response.get("check_runs") if isinstance(response, dict) else None
        if not isinstance(runs, list) or not all(isinstance(run, dict) for run in runs):
            raise ClientRefusal(
                "E-GITHUB-API-REFUSED", "check-runs listing lacked a check_runs list"
            )
        return runs

    def app_identity(self) -> dict[str, Any]:
        """Who this JWT is, from GitHub: id, slug, html_url."""

        response = self._request("GET", "/app", token=mint_app_jwt(self._credentials, now=self._now()))
        if not isinstance(response, dict) or type(response.get("id")) is not int:
            raise ClientRefusal("E-GITHUB-API-REFUSED", "GET /app lacked an integer id")
        return response

    def list_installations(self) -> list[dict[str, Any]]:
        """Every installation of this App the JWT can see."""

        response = self._request(
            "GET", "/app/installations", token=mint_app_jwt(self._credentials, now=self._now())
        )
        if not isinstance(response, list) or not all(isinstance(item, dict) for item in response):
            raise ClientRefusal(
                "E-GITHUB-API-REFUSED", "GET /app/installations was not a list of objects"
            )
        return response


def api_root_from_environment() -> str:
    """The API root: GitHub's, or the operator's Enterprise override."""

    return os.environ.get(API_ROOT_VARIABLE) or API_ROOT
