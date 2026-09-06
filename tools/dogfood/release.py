"""Prepare and publish padded patch releases for committed dogfood fixes.

`prepare` edits only package metadata and its frozen lock; it never commits.
`auto` runs from a clean, current main checkout after CI succeeds. It prepares
a release commit, runs the frozen suite ON that commit, builds real packages,
and pushes main plus its immutable tag atomically. No force pushes or retags.
The hosted job uses GITHUB_TOKEN and explicitly dispatches CI on the release tag.
Publication also creates a GitHub Release with verified distribution assets.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
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


def require_publisher() -> tuple[str, str]:
    """Use the job token in the owner-authorized workflow, the owner locally."""
    if os.environ.get("GITHUB_ACTIONS") != "true":
        require_owner()
        return OWNER, f"{OWNER}@users.noreply.github.com"
    expected = {
        "GITHUB_REPOSITORY": REPOSITORY,
        "GITHUB_EVENT_NAME": "workflow_run",
        "GITHUB_WORKFLOW_REF": (
            f"{REPOSITORY}/.github/workflows/dogfood-release.yml@refs/heads/main"
        ),
    }
    if any(os.environ.get(key) != value for key, value in expected.items()):
        raise ValueError("job-token publication requires the upstream Dogfood release workflow")
    repository = json.loads(command("gh", "api", f"repos/{REPOSITORY}"))
    if repository.get("full_name") != REPOSITORY:
        raise ValueError("release token does not identify the Ranex repository")
    return "github-actions[bot]", "41898282+github-actions[bot]@users.noreply.github.com"


def publish_release(tag: str, previous_tag: str, revision: str, source: str,
                    findings: list[str]) -> None:
    """Publish the already verified tag and the actual built distribution files."""
    version = package_version()
    directory = ROOT / ".local/release/dist"
    assets = [directory / f"ranex-{version}-py3-none-any.whl",
              directory / f"ranex-{version}.tar.gz"]
    hashes = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in assets}
    checksums = directory / "SHA256SUMS"
    checksums.write_text("".join(f"{digest}  {name}\n" for name, digest in hashes.items()))
    assets.append(checksums)
    hashes[checksums.name] = hashlib.sha256(checksums.read_bytes()).hexdigest()
    notes = ROOT / ".local/release/notes.txt"
    notes.write_text(
        f"Dogfood fixes: {', '.join(findings)}. Source commit: {source}.\n\n"
        f"Release commit: {revision}. `uv run --frozen pytest -q` passed on this "
        "commit before publication; named skips remain unverified. Wheel and sdist "
        "were built from this commit, and the remote branch/tag were verified.\n\n"
        f"Install from a source checkout using the [quickstart](https://github.com/"
        f"{REPOSITORY}/tree/{tag}#quickstart). Governed commands require a configured "
        "checkout; installing the wheel alone is not a governance environment.\n\n"
        f"The attached distributions use Python version {version}. SHA256SUMS "
        "covers the wheel and sdist. Full tag CI runs separately; inspect its "
        f"[result](https://github.com/{REPOSITORY}/actions/workflows/ci.yml) "
        "before relying on capabilities absent from the publishing runner.\n"
    )
    command("gh", "release", "create", tag, *(str(path) for path in assets),
            "--repo", REPOSITORY, "--verify-tag", "--title", tag,
            "--notes-file", str(notes), "--generate-notes", "--notes-start-tag", previous_tag,
            "--latest", capture=False)
    detail = json.loads(command("gh", "api", f"repos/{REPOSITORY}/releases/tags/{tag}"))
    latest = json.loads(command("gh", "api", f"repos/{REPOSITORY}/releases/latest"))
    uploaded = {asset["name"]: asset for asset in detail.get("assets", [])}
    if latest.get("tag_name") != tag or detail.get("draft") or detail.get("tag_name") != tag or any(
        uploaded.get(name, {}).get("digest") != f"sha256:{digest}"
        or uploaded.get(name, {}).get("state") != "uploaded"
        for name, digest in hashes.items()
    ):
        raise ValueError("GitHub Release was created but asset verification failed")
    print(f"GITHUB-RELEASE {detail['html_url']}; wheel/sdist/checksum digests verified")


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
    publisher, email = require_publisher()
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
    previous_tag = tag_for(package_version())
    tag = prepare()
    date = datetime.now(UTC).date().isoformat()
    (ROOT / "docs/STATE.md").write_text(
        f"# State\n\n**Updated:** {date}\n**Active slice:** none\n\n"
        f"Version {tag} follows dogfood fix {expected_head}.\n"
        f"Issues: {', '.join('#' + i for i in issues)}. Findings: {', '.join(findings)}.\n\n"
        "Publication requires the frozen suite on this commit and a real wheel/sdist build.\n"
        "The release workflow retains the validation logs. Source findings and their\n"
        "end-to-end receipts remain in tools/dogfood/FINDINGS.md and audits/.\n"
        "Hosted releases use GITHUB_TOKEN and explicitly dispatch CI on the published tag.\n"
        "GitHub Releases carry the wheel, sdist and verified SHA256SUMS for that tag.\n"
        "External services and host capabilities absent on the runner are UNVERIFIED.\n")
    readme = ROOT / "README.md"
    released, count = re.subn(
        r"\*\*Current release: \[\`?v[0-9]+\.[0-9]+\.[0-9]+\`?\]\(https://github\.com/anthonykewl20/ranex/(?:tree|releases/tag)/v[0-9]+\.[0-9]+\.[0-9]+\)",
        f"**Current release: [`{tag}`](https://github.com/{REPOSITORY}/releases/tag/{tag})",
        readme.read_text(),
    )
    if count != 1:
        raise ValueError("README does not identify exactly one current release")
    readme.write_text(released)
    command("git", "add", "pyproject.toml", "uv.lock", "docs/STATE.md", "README.md")
    command("git", "-c", f"user.name={publisher}", "-c", f"user.email={email}",
            "commit", "-m", f"release: {tag}\n\nDogfood-source: {expected_head}")
    revision = command("git", "rev-parse", "HEAD")
    # Run only after committing: metadata-only changes do not waive the owner gate.
    command("uv", "run", "--frozen", "pytest", "-q", capture=False)
    epoch = yaml.safe_load((ROOT / "governance/deps.yaml").read_text())["exclude_newer"]
    command("uv", "build", "--no-build-isolation", "--exclude-newer", str(epoch),
            "--out-dir", ".local/release/dist", capture=False)
    if command("git", "status", "--porcelain") or command("git", "rev-parse", "HEAD") != revision:
        raise ValueError("validation changed the release checkout")
    if require_publisher() != (publisher, email):
        raise ValueError("release publisher changed during validation")
    command("git", "-c", f"user.name={publisher}", "-c", f"user.email={email}",
            "tag", "-a", tag, "-m", f"{tag}: {', '.join(findings)}")
    command("git", "push", "--atomic", "origin", f"{revision}:refs/heads/main", f"refs/tags/{tag}",
            capture=False)
    tips = command("git", "ls-remote", "origin", "refs/heads/main", f"refs/tags/{tag}^{{}}")
    if len(tips.splitlines()) != 2 or any(row.split()[0] != revision for row in tips.splitlines()):
        raise ValueError("remote branch/tag verification failed")
    print(f"RELEASED {tag} {revision}; uv run --frozen pytest -q exit 0; wheel/sdist built")
    if publisher == "github-actions[bot]":
        # A built-in-token push deliberately does not cause another push run.
        # Dispatch the existing complete CI on the exact published tag instead.
        command("gh", "workflow", "run", "ci.yml", "--repo", REPOSITORY,
                "--ref", tag, "--raw-field", f"compare_base={expected_head}", capture=False)
        print(f"CI-DISPATCHED {tag}; release validation must finish in that workflow run")
    publish_release(tag, previous_tag, revision, expected_head, findings)


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
