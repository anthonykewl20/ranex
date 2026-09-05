"""Prepare and publish padded patch releases for committed dogfood fixes.

`prepare` edits only package metadata and its frozen lock; it never commits.
`auto` runs from a clean, current main checkout after CI succeeds. It prepares
a release commit, runs the frozen suite ON that commit, builds real packages,
and pushes main plus its immutable tag atomically. No force pushes or retags.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import subprocess
import tomllib
from datetime import UTC, datetime
from pathlib import Path

import yaml
from packaging.version import Version

from ranex.foundation.release_version import release_tag as tag_for

ROOT = Path(__file__).resolve().parents[2]
OWNER = "anthonykewl20"
REPOSITORY = f"{OWNER}/ranex"


def command(*argv: str, capture: bool = True) -> str:
    result = subprocess.run(argv, cwd=ROOT, text=True, check=True,
                            stdout=subprocess.PIPE if capture else None)
    return (result.stdout or "").strip()


def package_version() -> str:
    return tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]


def prepare() -> str:
    project = ROOT / "pyproject.toml"
    lock = ROOT / "uv.lock"
    if command("git", "diff", "HEAD", "--", "pyproject.toml", "uv.lock"):
        raise ValueError("package or lock already modified; commit or review it first")
    before_project, before_lock = project.read_bytes(), lock.read_bytes()
    before = tomllib.loads(before_lock.decode())
    current = package_version()
    tag_for(current)
    major, minor, patch = Version(current).release
    version = f"{major}.{minor + (patch == 999)}.{0 if patch == 999 else patch + 1}"
    tag = tag_for(version)
    # Check before editing metadata: an outdated checkout must refuse an
    # already published version without leaving a misleading candidate diff.
    exists = subprocess.run(["git", "show-ref", "--verify", "--quiet", f"refs/tags/{tag}"],
                            cwd=ROOT, check=False)
    if exists.returncode != 1:
        raise ValueError(f"tag already exists or cannot be checked: {tag}")
    epoch = yaml.safe_load((ROOT / "governance/deps.yaml").read_text())["exclude_newer"]
    try:
        old = f'version = "{current}"'
        if before_project.decode().count(old) != 1:
            raise ValueError("package version declaration is ambiguous")
        project.write_text(before_project.decode().replace(old, f'version = "{version}"'))
        command("uv", "lock", "--exclude-newer", str(epoch), capture=False)
        expected = copy.deepcopy(before)
        packages = [p for p in expected["package"] if p["name"] == "ranex"]
        if len(packages) != 1 or packages[0]["version"] != current:
            raise ValueError("lock does not identify the current Ranex package")
        packages[0]["version"] = version
        if tomllib.loads(lock.read_text()) != expected:
            raise ValueError("release re-lock changed dependencies or resolver policy")
    except BaseException:
        project.write_bytes(before_project)
        lock.write_bytes(before_lock)
        raise
    return tag


def require_owner() -> None:
    def active() -> bool:
        status = json.loads(command("gh", "auth", "status", "--active", "--hostname",
                                    "github.com", "--json", "hosts"))
        return any(row.get("login") == OWNER and row.get("active")
                   and row.get("state") == "success"
                   for row in status["hosts"].get("github.com", []))

    if not active():
        command("gh", "auth", "switch", "-h", "github.com", "-u", OWNER)
    if not active():
        raise ValueError("release requires the anthonykewl20 GitHub identity")


def auto(expected_head: str) -> None:
    if not re.fullmatch(r"[0-9a-f]{40}", expected_head):
        raise ValueError("expected head must be an exact commit SHA")
    if command("git", "status", "--porcelain"):
        raise ValueError("release requires a clean checkout")
    if command("git", "rev-parse", "HEAD") != expected_head:
        raise ValueError("checkout does not match the successful CI revision")
    message = command("git", "log", "-1", "--format=%B")
    findings = re.findall(r"^Dogfood-Fixes: (F-[0-9]{3}(?:, F-[0-9]{3})*)$", message, re.M)
    issues = re.findall(r"^Fixes #(\d+)$", message, re.M)
    if not findings or not issues:
        print("NO-RELEASE: commit has no Dogfood-Fixes and Fixes #issue trailers")
        return
    require_owner()
    # Restrict publication to this project's actual upstream, never a PR fork.
    remote = command("git", "remote", "get-url", "origin")
    if remote not in {f"https://github.com/{REPOSITORY}.git",
                      f"https://github.com/{REPOSITORY}",
                      f"git@github.com:{REPOSITORY}.git"}:
        raise ValueError("origin is not the Ranex release repository")
    command("git", "fetch", "origin", "main", "--tags")
    if command("git", "rev-parse", "origin/main") != expected_head:
        print("NO-RELEASE: main has advanced; its newer CI run owns publication")
        return
    for issue in issues:
        detail = json.loads(command("gh", "issue", "view", issue, "--repo", REPOSITORY,
                                    "--json", "number"))
        if detail["number"] != int(issue):
            raise ValueError("fix does not identify a real repository issue")
    tag = prepare()
    date = datetime.now(UTC).date().isoformat()
    (ROOT / "docs/STATE.md").write_text(
        f"# State\n\n**Updated:** {date}\n**Active slice:** none\n\n"
        f"Version {tag} follows dogfood fix {expected_head}.\n"
        f"Issues: {', '.join('#' + i for i in issues)}. Findings: {', '.join(findings)}.\n\n"
        "Publication requires the frozen suite on this commit and a real wheel/sdist build.\n"
        "The release workflow retains the validation logs. Source findings and their\n"
        "end-to-end receipts remain in tools/dogfood/FINDINGS.md and audits/.\n"
        "External services and host capabilities absent on the runner are UNVERIFIED.\n")
    readme = ROOT / "README.md"
    released, count = re.subn(
        r"\*\*Current release: \[\`?v[0-9]+\.[0-9]+\.[0-9]+\`?\]\(https://github\.com/anthonykewl20/ranex/tree/v[0-9]+\.[0-9]+\.[0-9]+\)",
        f"**Current release: [`{tag}`](https://github.com/{REPOSITORY}/tree/{tag})",
        readme.read_text(),
    )
    if count != 1:
        raise ValueError("README does not identify exactly one current release")
    readme.write_text(released)
    command("git", "add", "pyproject.toml", "uv.lock", "docs/STATE.md", "README.md")
    command("git", "-c", f"user.name={OWNER}", "-c", f"user.email={OWNER}@users.noreply.github.com",
            "commit", "-m", f"release: {tag}\n\nDogfood-source: {expected_head}")
    revision = command("git", "rev-parse", "HEAD")
    # Run only after committing: metadata-only changes do not waive the owner gate.
    command("uv", "run", "--frozen", "pytest", "-q", capture=False)
    epoch = yaml.safe_load((ROOT / "governance/deps.yaml").read_text())["exclude_newer"]
    command("uv", "build", "--no-build-isolation", "--exclude-newer", str(epoch),
            "--out-dir", ".local/release/dist", capture=False)
    if command("git", "status", "--porcelain") or command("git", "rev-parse", "HEAD") != revision:
        raise ValueError("validation changed the release checkout")
    require_owner()
    command("git", "-c", f"user.name={OWNER}", "-c", f"user.email={OWNER}@users.noreply.github.com",
            "tag", "-a", tag, "-m", f"{tag}: {', '.join(findings)}")
    command("git", "push", "--atomic", "origin", f"{revision}:refs/heads/main", f"refs/tags/{tag}",
            capture=False)
    tips = command("git", "ls-remote", "origin", "refs/heads/main", f"refs/tags/{tag}^{{}}")
    if len(tips.splitlines()) != 2 or any(row.split()[0] != revision for row in tips.splitlines()):
        raise ValueError("remote branch/tag verification failed")
    print(f"RELEASED {tag} {revision}; uv run --frozen pytest -q exit 0; wheel/sdist built")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("prepare")
    sub.add_parser("version")
    automatic = sub.add_parser("auto")
    automatic.add_argument("--expected-head", required=True)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            print(prepare())
        elif args.command == "version":
            print(tag_for(package_version()))
        else:
            auto(args.expected_head)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"RELEASE-REFUSED: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
