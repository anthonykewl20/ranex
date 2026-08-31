"""Unit tests for retained execution-log redaction."""

from __future__ import annotations

import pytest

from ranex.execution.log_redaction import collect_redaction_literals, redact_text


@pytest.mark.parametrize("label", ("RSA ", "EC ", "OPENSSH ", "ENCRYPTED "))
def test_redact_text_scrubs_labeled_pem_blocks(label: str) -> None:
    block = f"-----BEGIN {label}PRIVATE KEY-----\nsecret-material\n-----END {label}PRIVATE KEY-----"

    redacted, counts = redact_text(f"before\n{block}\nafter", ())

    assert redacted == "before\n[REDACTED:pem]\nafter"
    assert counts == {"pem": 1}


def test_redact_text_scrubs_multiple_pem_blocks() -> None:
    rsa = "-----BEGIN RSA PRIVATE KEY-----\nrsa\n-----END RSA PRIVATE KEY-----"
    ec = "-----BEGIN EC PRIVATE KEY-----\nec\n-----END EC PRIVATE KEY-----"

    redacted, counts = redact_text(f"{rsa}\nnot-a-key\n{ec}", ())

    assert redacted == "[REDACTED:pem]\nnot-a-key\n[REDACTED:pem]"
    assert counts == {"pem": 2}


def test_redact_text_scrubs_credential_url_passwords_only() -> None:
    text = "https://ci:pw123@registry.invalid/x git+https://bot:token@github.invalid/repo"

    redacted, counts = redact_text(text, ())

    assert redacted == (
        "https://ci:[REDACTED:credential]@registry.invalid/x "
        "git+https://bot:[REDACTED:credential]@github.invalid/repo"
    )
    assert counts == {"credential": 2}


def test_redact_text_leaves_plain_urls_unchanged() -> None:
    text = "https://registry.invalid/x git+https://github.invalid/repo"

    assert redact_text(text, ()) == (text, {})


def test_collect_redaction_literals_applies_floors_deduplicates_and_sorts() -> None:
    ambient = {
        "ALPHA_TOKEN": "a" * 20,
        "OPENROUTER_API_KEY": "b" * 16,
        "RANEX_SIGNING_KEY": "c" * 18,
        "MANUAL": "d" * 18,
        "SHORT_SECRET": "e" * 15,
        "UNRELATED": "f" * 32,
    }

    literals = collect_redaction_literals(ambient, forced=("MANUAL", "MANUAL"))

    assert literals == [
        ("env:ALPHA_TOKEN", "a" * 20),
        ("env:MANUAL", "d" * 18),
        ("env:RANEX_SIGNING_KEY", "c" * 18),
        ("env:OPENROUTER_API_KEY", "b" * 16),
    ]


def test_collect_redaction_literals_refuses_missing_forced_name() -> None:
    with pytest.raises(
        ValueError,
        match=r"^refusing --redact-env NOT_SET: not set in the environment$",
    ):
        collect_redaction_literals({}, forced=("NOT_SET",))


def test_collect_redaction_literals_refuses_short_forced_value() -> None:
    with pytest.raises(
        ValueError,
        match=(
            r"^refusing --redact-env SHORT: value shorter than the 16-byte redaction floor$"
        ),
    ):
        collect_redaction_literals({"SHORT": "x" * 15}, forced=("SHORT",))


def test_redact_text_counts_are_exact_and_deterministic() -> None:
    literals = [("env:TOKEN", "token-value-1234")]
    text = "token-value-1234 and token-value-1234"

    first = redact_text(text, literals)
    second = redact_text(text, literals)

    assert first == ("[REDACTED:env:TOKEN] and [REDACTED:env:TOKEN]", {"env:TOKEN": 2})
    assert second == first


def test_redact_text_prefers_longest_overlapping_literal() -> None:
    redacted, counts = redact_text(
        "prefix abcdefghijklmnopq suffix",
        (("env:LONG", "abcdefghijklmnopq"), ("env:SHORT", "abcdefghijklmnop")),
    )

    assert redacted == "prefix [REDACTED:env:LONG] suffix"
    assert counts == {"env:LONG": 1}


def test_redact_text_removes_secret_inside_pem_block_without_remaining_hits() -> None:
    secret = "secret-value-1234"
    block = (
        "-----BEGIN RSA PRIVATE KEY-----\n"
        f"{secret}\n"
        "-----END RSA PRIVATE KEY-----"
    )

    redacted, counts = redact_text(block, (("env:SECRET", secret),))

    assert secret not in redacted
    assert redacted == "[REDACTED:pem]"
    assert counts == {"env:SECRET": 1, "pem": 1}


def test_redact_text_handles_non_ascii_hostile_and_no_hit_text() -> None:
    text = "雪だるま\x00\ud800 https://example.invalid/🙂"

    assert redact_text(text, ()) == (text, {})
