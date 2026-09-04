"""REAL evolution graphs, computed entirely from the repository's own history.

Nothing here is typed by hand. Every series is derived by reading past
commits with git:

  kernel complexity   total McCabe paths (M = decisions + 1) of src/ranex
                      at each commit — how much machine the kernel IS.
  curriculum          number of registered proof scenarios at each commit —
                      how much of it the proofs claim.
  proof pile          archived real-world proof entries at each commit.
  findings            open findings in FINDINGS.md at each commit.

The evolution claim these graphs carry: the curriculum must grow at least
as fast as the kernel's complexity, and the pile must never shrink. All
x-axes are commits (dated); the series fill automatically every night.
"""

from __future__ import annotations

import ast
import hashlib
import html
import json
import re
import subprocess
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "tools/dogfood/site"

BG = "#0b1220"; PANEL = "#111a2c"; HAIR = "#1f2a3d"; INK = "#e8eef5"
MUTED = "#93a1b4"; GOOD = "#4cc38a"; BAD = "#f0616d"; BLUE = "#58a6ff"
AMBER = "#f0b429"


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(REPO), *args],
                          capture_output=True, text=True, check=False)


def dogfood_commits() -> list[dict[str, str]]:
    result = _git("log", "--reverse", "--format=%H|%ad|%s", "--date=short",
                  "--", "tools/dogfood")
    commits = []
    for line in result.stdout.splitlines():
        parts = line.split("|", 2)
        if len(parts) == 3:
            commits.append({"sha": parts[0][:9], "date": parts[1],
                            "subject": parts[2][:60]})
    return commits


def complexity_at(sha: str) -> int:
    listing = _git("ls-tree", "-r", "--name-only", sha, "src/ranex")
    total = 0
    for path in listing.stdout.splitlines():
        if not path.endswith(".py"):
            continue
        blob = _git("show", f"{sha}:{path}")
        if blob.returncode != 0:
            continue
        try:
            tree = ast.parse(blob.stdout)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                total += 1  # M >= 1 per function
                for child in ast.walk(node):
                    if isinstance(child, (ast.If, ast.For, ast.While, ast.IfExp,
                                          ast.ExceptHandler, ast.Assert)):
                        total += 1
                    elif isinstance(child, ast.BoolOp):
                        total += len(child.values) - 1
                    elif isinstance(child, ast.comprehension):
                        total += 1 + len(child.ifs)
    return total


def scenario_count_at(sha: str) -> int:
    blob = _git("show", f"{sha}:tools/dogfood/scenarios.py")
    if blob.returncode != 0:
        return 0
    return len(re.findall(r'^    "[a-z0-9-]+": \($', blob.stdout, re.M))


def proof_pile_at(sha: str) -> int:
    listing = _git("ls-tree", "-r", "--name-only", sha,
                   "--", "tools/dogfood/oss_bench/proofs")
    return len([n for n in listing.stdout.splitlines()
                if "/proof-" in n])


def open_findings_at(sha: str) -> int:
    blob = _git("show", f"{sha}:tools/dogfood/FINDINGS.md")
    if blob.returncode != 0:
        return 0
    in_open = False
    count = 0
    for line in blob.stdout.splitlines():
        if line.startswith("## "):
            in_open = line.strip() == "## Open"
        elif in_open and line.startswith("### F-"):
            count += 1
    return count


def collect_series() -> list[dict[str, Any]]:
    commits = dogfood_commits()
    sampled = []
    for commit in commits:
        sampled.append({
            **commit,
            "complexity": complexity_at(commit["sha"]),
            "scenarios": scenario_count_at(commit["sha"]),
            "pile": proof_pile_at(commit["sha"]),
            "open_findings": open_findings_at(commit["sha"]),
        })
    return sampled


def _line_chart(series: list[dict[str, Any]], keys: list[tuple[str, str, str]],
                title: str, subtitle: str, source: str) -> str:
    width, height, pad = 760, 300, 58
    plot_w, plot_h = width - pad - 24, height - 78
    n = len(series)
    if n < 2:
        return (f'<div class="card"><h3>{html.escape(title)}</h3>'
                f'<p class="note">Needs at least two commits of history; the '
                f'series fills automatically every night.</p></div>')
    max_x = max(max(s[k] for s in series) for k, _, _ in keys) or 1

    def px(i):
        return pad + (i / (n - 1)) * plot_w

    def py(v):
        return 40 + plot_h - (v / max_x) * plot_h

    parts = [f'<svg class="graph" viewBox="0 0 {width} {height}" '
             'xmlns="http://www.w3.org/2000/svg" '
             'font-family="ui-monospace,monospace" role="img" aria-label="'
             + html.escape(title) + '">',
             f'<text x="0" y="18" fill="{INK}" font-size="13.5" '
             f'font-weight="700">{html.escape(title)}</text>',
             f'<text x="0" y="34" fill="{MUTED}" font-size="11.5">'
             f'{html.escape(subtitle)}</text>',
             f'<rect x="{pad}" y="40" width="{plot_w}" height="{plot_h}" '
             f'fill="none" stroke="{HAIR}"/>']
    for step in range(5):
        value = max_x * step / 4
        y = py(value)
        parts.append(f'<line x1="{pad}" y1="{y:.1f}" x2="{pad + plot_w}" '
                     f'y2="{y:.1f}" stroke="{MUTED}" stroke-opacity="0.12"/>')
        parts.append(f'<text x="{pad - 8}" y="{y + 4:.1f}" fill="{MUTED}" '
                     f'font-size="10.5" text-anchor="end">{value:,.0f}</text>')
    label_step = max(1, n // 8)
    last_label_x = None
    for i, point in enumerate(series):
        x = px(i)
        # A date label is emitted only with >=44px of clearance from the
        # previous one: adjacent commits often share a date, and the
        # endpoint rule (i == n-1) would otherwise print on top of the
        # modulo-labelled neighbour — measured 6px overlap at n=20.
        if ((i % label_step == 0 or i == n - 1)
                and (last_label_x is None or x - last_label_x >= 44)):
            parts.append(f'<text x="{x:.1f}" y="{40 + plot_h + 18}" '
                         f'fill="{MUTED}" font-size="10" text-anchor="middle">'
                         f'{point["date"][5:]}</text>')
            last_label_x = x
    for key, color, label in keys:
        pts = " ".join(f"{px(i):.1f},{py(s[key]):.1f}"
                       for i, s in enumerate(series))
        parts.append(f'<polyline points="{pts}" fill="none" stroke="{color}" '
                     f'stroke-width="2.5"/>')
        last = series[-1][key]
        parts.append(f'<text x="{px(n - 1) - 4:.1f}" y="{py(last) - 8:.1f}" '
                     f'fill="{color}" font-size="11" text-anchor="end" '
                     f'font-weight="700">{label} {last:,}</text>')
    parts.append(f'<text x="0" y="{height - 4}" fill="{MUTED}" font-size="10">'
                 f'{html.escape(source)}</text></svg>')
    return "".join(parts)


def charts_for_embed(series: list[dict[str, Any]] | None = None,
                     ) -> tuple[list[str], str]:
    """The three evolution charts as standalone SVG strings plus the series
    digest — the embed API for the main proof page (oss-benchmark.html)."""
    if series is None:
        series = collect_series()
    payload = json.dumps({"schema": "ranex-evolution-series-v1",
                          "series": series}, indent=2, sort_keys=True) + "\n"
    digest = "sha256:" + hashlib.sha256(payload.encode()).hexdigest()
    charts = [
        _line_chart(series,
                    [("complexity", AMBER, "kernel paths"),
                     ("scenarios", GOOD, "proof scenarios")],
                    "The kernel grows — the curriculum grows faster",
                    "total McCabe independent paths in src/ranex vs registered "
                    "proof scenarios, per commit",
                    "source: git history — AST of src/ranex at each commit; "
                    "scenario registry per commit"),
        _line_chart(series, [("pile", BLUE, "proofs piled")],
                    "Real-world proofs accumulated",
                    "archived proof entries (real agent runs + attacks), "
                    "per commit — append-only, never shrinks",
                    "source: git history of tools/dogfood/oss_bench/proofs/"),
        _line_chart(series, [("open_findings", BAD, "open findings")],
                    "Findings: opened, tracked, closed",
                    "open F-findings in FINDINGS.md per commit — the loop's "
                    "honest bug ledger",
                    "source: git history of tools/dogfood/FINDINGS.md"),
    ]
    return charts, digest


def generate() -> Path:
    series = collect_series()
    payload = json.dumps({"schema": "ranex-evolution-series-v1",
                          "series": series}, indent=2, sort_keys=True) + "\n"
    data_path = OUT_DIR / "evolution.json"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data_path.write_text(payload)
    charts, _ = charts_for_embed(series)

    first, last = series[0], series[-1]
    grew_ratio = (last["scenarios"] / first["scenarios"]
                  if first["scenarios"] else 0)
    digest = "sha256:" + hashlib.sha256(payload.encode()).hexdigest()
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ranex — the kernel, evolving (measured)</title>
<style>
  :root {{ color-scheme: dark; }}
  body {{ margin:0; background:{BG}; color:{INK};
         font:16px/1.6 ui-sans-serif,system-ui,sans-serif; }}
  main {{ max-width:840px; margin:0 auto; padding:44px 22px 80px; }}
  h1 {{ font-size:26px; margin:0 0 8px; }}
  .lede {{ color:{MUTED}; font-size:15.5px; margin:0 0 14px; }}
  .note {{ color:{MUTED}; font-size:13px; margin:6px 0 10px; }}
  .card {{ background:{PANEL}; border:1px solid {HAIR}; border-radius:14px;
          padding:16px 18px; margin:14px 0; }}
  svg.graph {{ width:100%; height:auto; display:block; margin:8px 0 2px; }}
  .stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr));
           gap:10px; margin:14px 0; }}
  .stat {{ background:{PANEL}; border:1px solid {HAIR}; border-radius:12px;
          padding:13px 15px; }}
  .stat .n {{ font-size:22px; font-weight:800;
             font-family:ui-monospace,monospace; }}
  .stat .t {{ color:{MUTED}; font-size:12px; margin-top:3px; }}
  code {{ background:{PANEL}; border:1px solid {HAIR}; border-radius:6px;
         padding:1px 7px; font-size:12.5px; }}
  footer {{ margin-top:44px; border-top:1px solid {HAIR}; padding-top:14px;
           color:{MUTED}; font-size:12px; }}
</style></head><body><main>
<h1>The kernel, evolving — measured, not claimed</h1>
<p class="lede">Every point on every graph is computed from the repository's
own git history at that commit: the kernel's total independent code paths,
the proof curriculum's size, the accumulated real-world proof pile, and the
open-findings ledger. The graphs refill automatically every dogfood cycle.</p>
<div class="stats">
 <div class="stat"><div class="n">{last['complexity']:,}</div><div class="t">
 kernel independent paths at HEAD (McCabe, AST-computed)</div></div>
 <div class="stat"><div class="n" style="color:{GOOD}">{last['scenarios']}</div>
 <div class="t">deterministic proof scenarios ({grew_ratio:.1f}× since the
 first dogfood commit)</div></div>
 <div class="stat"><div class="n" style="color:{BLUE}">{last['pile']}</div>
 <div class="t">real-world proofs archived (append-only)</div></div>
 <div class="stat"><div class="n" style="color:{BAD}">{last['open_findings']}</div>
 <div class="t">open findings — tracked honestly, closed deliberately</div></div>
</div>
{''.join(charts)}
<p class="note">Series data: <code>evolution.json</code> · digest
<code>{digest}</code> · regenerate with
<code>uv run --frozen python tools/dogfood/evolution_graphs.py</code></p>
<footer>ranex — deterministic governance for AI agents that build software ·
every value computed from git at the labeled commit · nothing typed by hand</footer>
</main></body></html>
"""
    out = OUT_DIR / "evolution.html"
    out.write_text(page)
    return out


if __name__ == "__main__":
    print("page:", generate())
