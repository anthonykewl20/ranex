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
import time
import urllib.error
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
    """Parse the App's PEM key, refusing anything unreadable."""

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
        payload = None if body is None else json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            f"{self._api_root}{path}",
            data=payload,
            method=method,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": MEDIA_TYPE,
                "Content-Type": MEDIA_TYPE,
                "X-GitHub-Api-Version": API_VERSION,
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self._timeout) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            # The body may name the reason (bad credentials, missing
            # permission); surface its first bytes, never a secret — the
            # request's own headers are not echoed into the refusal.
            detail = exc.read()[:200].decode("utf-8", "replace").strip()
            raise ClientRefusal(
                "E-GITHUB-API-REFUSED",
                f"{method} {path}: HTTP {exc.code} {detail}",
            ) from exc
        except (urllib.error.URLError, OSError) as exc:
            raise ClientRefusal(
                "E-GITHUB-API-REFUSED", f"{method} {path}: {exc}"
            ) from exc
        return json.loads(raw) if raw else {}

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
        owner, separator, name = repository.partition("/")
        if not owner or not separator or not name:
            raise ClientRefusal(
                "E-GITHUB-BAD-REPO", f"expected owner/name: {repository!r}"
            )
        return self._request(
            "POST",
            f"/repos/{owner}/{name}/check-runs",
            token=self.installation_token(installation_id),
            body=body,
        )


def api_root_from_environment() -> str:
    """The API root: GitHub's, or the operator's Enterprise override."""

    return os.environ.get(API_ROOT_VARIABLE) or API_ROOT
