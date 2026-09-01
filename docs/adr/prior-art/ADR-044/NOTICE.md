# Prior-art notice

- `systemd-v257-systemd-run.xml` — origin: https://github.com/systemd/systemd/blob/v257/man/systemd-run.xml (tag v257); LGPL-2.1-or-later (SPDX header in the file). Copied as decision evidence only: no product code in this repository is derived from it. Blob of the retained copy: 20c0a5af2ea84ef1760934f7128f21ed6a18c998.
- `linux-v6.12-cgroup-v2-delegation-excerpt.rst` — origin: https://github.com/torvalds/linux/blob/v6.12/Documentation/admin-guide/cgroup-v2.rst (tag v6.12); GPL-2.0 (kernel Documentation). EXCERPT: sections 1–2 only (Introduction and Basic Operations, including 2-5 Delegation and 2-6 Guidelines); sections 3 onward were omitted. Copied as decision evidence only. Blob of the retained copy: cc934a14c1c8e03a436ca72a611d4147c07bdae0.

Fetch-method disclosure: this session's bash was restricted to
`git status`/`git diff`/`claude`, so `curl` against raw.githubusercontent.com
was unavailable. Both files were obtained through the harness webfetch
tool in text mode on 2026-09-01 and written from the fetched text; the
blob hashes above are git blob hashes OF THE RETAINED COPIES (computed via
`git diff --no-index --full-index /dev/null <file>`). Because a text-mode
fetch may normalize whitespace and cannot be byte-compared against the raw
upstream objects here, byte-identity to upstream is UNVERIFIED — a
verifier with network access should re-fetch at the pinned tags and
compare blob hashes before treating the copies as raw upstream objects.
No product code in this repository is copied from these vendored sources.
