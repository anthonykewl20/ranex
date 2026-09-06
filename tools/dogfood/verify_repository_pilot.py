"""Reconstruct a pilot tree and verify its archived verdict without private keys.

The included public key is evidence, not an independently trusted identity.
An operator must review/anchor that identity before relying on the decision.
Only a temporary Git index and loose objects are written; no checkout or ref
is changed, and no repository code is executed.
"""

from __future__ import annotations

import argparse
import json
import re
import tempfile
from pathlib import Path

from ranex.bootstrap.composition import catalog_digest_for
from ranex.cli.repository import git
from ranex.github_app.binding import subject_digest_for_tree
from ranex.governed_execution.verdict_reader import ReadState, read_verdict
from ranex.policy.adapters.configuration.yaml.producer_keyring import load_trust_keyring_text


def verify(receipt_path: Path, repository: Path) -> tuple[str, str]:
    receipt = json.loads(receipt_path.read_bytes())
    upstream = receipt["upstream_commit"]
    expected = receipt["verification_material"]["tree"]
    if any(not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{40}", value) is None
           for value in (upstream, expected)):
        raise ValueError("receipt must contain exact commit/tree object IDs")
    material = receipt_path.parent / (receipt_path.stem + "-verification")
    with tempfile.TemporaryDirectory(prefix="ranex-pilot-verifier-") as scratch:
        overrides = {"GIT_INDEX_FILE": str(Path(scratch) / "index")}
        for arguments in (
            ("read-tree", upstream),
            ("apply", "--cached", str((material / "pilot.patch").resolve())),
        ):
            result = git(repository, *arguments, overrides=overrides)
            if result.returncode:
                raise ValueError(f"source reconstruction refused: {result.stderr.strip()}")
        result = git(repository, "write-tree", overrides=overrides)
        if result.returncode or result.stdout.strip() != expected:
            raise ValueError("reconstructed source tree does not match the receipt")

    # The public policy files beside the verdict must be the files in the
    # reconstructed subject; otherwise the archive could tell two stories.
    for name in ("gates.yaml", "producers.yaml", "suite_manifest.json"):
        result = git(repository, "show", f"{expected}:governance/{name}", text=False)
        if result.returncode or result.stdout != (material / name).read_bytes():
            raise ValueError(f"archived {name} differs from the reconstructed source")
    keyring = load_trust_keyring_text(
        (material / "producers.yaml").read_text(), material / "producers.yaml",
    )
    verdict = read_verdict(
        material / "verdict.json",
        {keyring.verdict_signer_id: keyring.verdict_signer_public_key},
        subject_digest=subject_digest_for_tree(expected), gate_id="landing",
        catalog_digest=catalog_digest_for((material / "gates.yaml").read_bytes()),
        approver_id="pilot-owner",
    )
    if verdict.state is not ReadState.VERIFIED or verdict.record is None:
        raise ValueError(f"archived verdict refused: {verdict.state.value}")
    return expected, str(verdict.record["verdict"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--repository", type=Path, required=True,
                        help="local Git repository containing the recorded upstream commit")
    args = parser.parse_args()
    try:
        tree, verdict = verify(args.receipt.resolve(), args.repository.resolve())
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"REFUSED  {error}")
        return 1
    print(f"VERIFIED  tree={tree}  recorded-verdict={verdict}")
    print("SIGNATURE  valid under archived public key; identity trust requires operator review")
    print("SCOPE  archive integrity only; tests were not rerun and GitHub enforcement is UNVERIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
