# Vendored prior art for ADR-031

Copied verbatim for review. No file here is imported, executed, adapted, or
relicensed as Ranex product code; these files are evidence that the cited
implementations were read.

| File | Origin | Licence |
|---|---|---|
| `git-tr2_dst.c` | <https://raw.githubusercontent.com/git/git/v2.45.2/trace2/tr2_dst.c> (tag `v2.45.2`) | **GPL-2.0** |
| `git-tr2_tgt_event.c` | <https://raw.githubusercontent.com/git/git/v2.45.2/trace2/tr2_tgt_event.c> (tag `v2.45.2`) | **GPL-2.0** |
| `git-tr2_sid.c` | <https://raw.githubusercontent.com/git/git/v2.45.2/trace2/tr2_sid.c> (tag `v2.45.2`) | **GPL-2.0** |
| `pino-redaction.js` | <https://raw.githubusercontent.com/pinojs/pino/v9.4.0/lib/redaction.js> (tag `v9.4.0`) | MIT |
| `structlog-native.py` | <https://raw.githubusercontent.com/hynek/structlog/24.4.0/src/structlog/_native.py> (tag `24.4.0`) | MIT OR Apache-2.0 |

**GPL WARNING:** the three `git` files remain GPL-2.0. They are pattern
evidence only — no code from them enters `src/` (ADR-012 precedent for vendored
git sources). They are not covered by Ranex's MIT licence and must not be
copied, adapted, linked, or incorporated into MIT product code without a
separate licensing review. They are retained here solely as unexecuted research
evidence.

Vendoring proves these bytes were obtained; it does not prove they came from
the stated URLs. Confirming provenance requires a second, independent fetch of
each cited URL, which the offline suite cannot perform.
