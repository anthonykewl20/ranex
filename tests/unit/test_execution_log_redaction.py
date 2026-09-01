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


def test_redact_text_scrubs_unpaired_pem_block_to_end_of_cut_stream() -> None:
    block = "-----BEGIN RSA PRIVATE KEY-----\nfirst-key-line\nsecond-key-line"

    redacted, counts = redact_text(block, ())

    assert redacted == "[REDACTED:pem]"
    assert "first-key-line" not in redacted
    assert "second-key-line" not in redacted
    assert counts == {"pem": 1}


def test_redact_text_keeps_paired_pem_redaction_idempotent() -> None:
    block = "-----BEGIN RSA PRIVATE KEY-----\nsecret-material\n-----END RSA PRIVATE KEY-----"

    first = redact_text(block, ())
    second = redact_text(first[0], ())

    assert first == ("[REDACTED:pem]", {"pem": 1})
    assert second == (first[0], {})


def test_redact_text_combines_paired_and_unpaired_pem_counts() -> None:
    paired = "-----BEGIN RSA PRIVATE KEY-----\npaired\n-----END RSA PRIVATE KEY-----"
    unpaired = "-----BEGIN EC PRIVATE KEY-----\nunpaired"

    redacted, counts = redact_text(f"{paired}\n{unpaired}", ())

    assert redacted == "[REDACTED:pem]\n[REDACTED:pem]"
    assert counts == {"pem": 2}


def test_redact_text_scrubs_crlf_pem_blocks() -> None:
    block = "-----BEGIN RSA PRIVATE KEY-----\r\nsecret-material\r\n-----END RSA PRIVATE KEY-----"

    redacted, counts = redact_text(block, ())

    assert redacted == "[REDACTED:pem]"
    assert counts == {"pem": 1}


def test_redact_text_scrubs_credential_url_passwords_only() -> None:
    text = "https://ci:pw123@registry.invalid/x git+https://bot:token@github.invalid/repo"

    redacted, counts = redact_text(text, ())

    assert redacted == (
        "https://ci:[REDACTED:credential]@registry.invalid/x "
        "git+https://bot:[REDACTED:credential]@github.invalid/repo"
    )
    assert counts == {"credential": 2}


def test_redact_text_scrubs_credential_url_passwords_containing_slashes() -> None:
    password = "pa/ss"
    text = f"https://user:{password}@registry.invalid/x"

    redacted, counts = redact_text(text, ())

    assert password not in redacted
    assert redacted == "https://user:[REDACTED:credential]@registry.invalid/x"
    assert counts == {"credential": 1}


def test_redact_text_scrubs_credential_url_passwords_containing_at_signs() -> None:
    password = "pa@ss"
    text = f"https://user:{password}@registry.invalid/x"

    first = redact_text(text, ())
    second = redact_text(text, ())

    assert all(fragment not in first[0] for fragment in ("pa", "ss"))
    assert first == ("https://user:[REDACTED:credential]@registry.invalid/x", {"credential": 1})
    assert second == first


def test_redact_text_scrubs_credential_url_password_before_extra_at_sign() -> None:
    password = "pass"
    text = f"https://user:{password}@@host/x"

    redacted, counts = redact_text(text, ())

    assert password not in redacted
    assert "[REDACTED:credential]" in redacted
    assert counts == {"credential": 1}


@pytest.mark.parametrize(
    "text",
    ("https://u:p@/x", "https://u:p@@/x"),
)
def test_redact_text_leaves_empty_credential_url_hosts_unchanged(text: str) -> None:
    assert redact_text(text, ()) == (text, {})


def test_redact_text_conservatively_over_redacts_at_bearing_url_paths() -> None:
    text = "https://user:password@registry.invalid/path@segment"

    redacted, counts = redact_text(text, ())

    assert redacted == "https://user:[REDACTED:credential]@segment"
    assert counts == {"credential": 1}


def test_redact_text_scrubs_multiple_credential_urls_in_one_line() -> None:
    text = "https://one:first@one.invalid/x https://two:second@two.invalid/y"

    redacted, counts = redact_text(text, ())

    assert redacted == (
        "https://one:[REDACTED:credential]@one.invalid/x "
        "https://two:[REDACTED:credential]@two.invalid/y"
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
