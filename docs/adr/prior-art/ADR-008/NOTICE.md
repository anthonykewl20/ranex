# Third-party source vendored for ADR-008

These files are copies of upstream implementations, kept so that what ADR-008
claims to have read is on disk and checkable. They are evidence, not
dependencies: nothing imports, executes or lints them.

Each was fetched at the pinned revision named below, and its git blob hash was
then compared against the hash the origin repository reports for that path at
that revision — so these copies agree with upstream, not merely with each other.
That agreement proves the bytes were obtained and match the cited path; it does
not, by itself, prove they came from that URL — provenance would need a second,
independent fetch, which this offline suite cannot perform (see CLAUDE.md).

- `opencode-plugin-hooks.ts` — MIT — opencode `packages/plugin/src/index.ts` at tag v1.18.11, commit 012c2f57f976489d88bd4598a056b4bdcdd428ee, blob `edfa0139dfcaf0e877ab906fabe8e0527afc3915`, from <https://github.com/anomalyco/opencode/blob/012c2f57f976489d88bd4598a056b4bdcdd428ee/packages/plugin/src/index.ts> — the hook contract the kernel bridge collects through.
- `pre-commit-run.py` — MIT — pre-commit `pre_commit/commands/run.py` at tag v4.6.1, commit 242ce8a25657be59f2770b50de41fe0fd508820d, blob `8ab505ffbeb79949dbf00d4606e4e0200c15f7b7`, from <https://github.com/pre-commit/pre-commit/blob/242ce8a25657be59f2770b50de41fe0fd508820d/pre_commit/commands/run.py> — Copyright (c) 2014 pre-commit dev team; the mature hook-drives-external-judging-of-a-diff pattern.

Both licences are MIT and compatible with this repository's MIT licence, and
both require the copyright notice to travel with the copy — which is what this
file is for.
