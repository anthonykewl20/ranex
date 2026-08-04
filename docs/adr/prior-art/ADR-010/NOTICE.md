# Vendored prior art for ADR-010

Copied verbatim for review. No file here is imported, executed, or adapted
into this tree; they are evidence that the cited implementations were read.

| File | Origin | Licence |
|---|---|---|
| `opencode-run-headless.ts` | <https://raw.githubusercontent.com/anomalyco/opencode/v1.18.12/packages/opencode/src/cli/cmd/run.ts> | MIT |
| `bors-ng-batcher.ex` | <https://raw.githubusercontent.com/bors-ng/bors-ng/ca725797e53a88e954998de0bbb14a8a5acb13ab/lib/worker/batcher.ex> | Apache-2.0 |
| `swe-agent-run-single.py` | <https://raw.githubusercontent.com/SWE-agent/SWE-agent/v1.1.0/sweagent/run/run_single.py> | MIT |
| `zuul-dependent-pipeline-manager.py` | <https://opendev.org/zuul/zuul/raw/commit/37b54283676b372740cd3f33b85171ac677da9de/zuul/manager/dependent.py> | Apache-2.0 |
| `openhands-headless-main.py` | <https://raw.githubusercontent.com/OpenHands/OpenHands/0.59.0/openhands/core/main.py> | MIT |
| `slsa-builder-go-two-job-split.yml` | <https://raw.githubusercontent.com/slsa-framework/slsa-github-generator/4d014fae4dbd39eb09e8d40348b73db095e6ba9a/.github/workflows/builder_go_slsa3.yml> | Apache-2.0 |
| `in-toto-sign.py` | <https://raw.githubusercontent.com/in-toto/in-toto/c82fe5d21aaa61c7f1a213db20a46f10bb3f411a/in_toto/in_toto_sign.py> | Apache-2.0 |
| `tekton-chains-taskrun-observe-then-sign.go` | <https://raw.githubusercontent.com/tektoncd/chains/01d9ebfdae7a02247b1b00f48e44dd63d8a611ec/pkg/reconciler/taskrun/taskrun.go> | Apache-2.0 |

Five files are Apache-2.0 rather than MIT. Both licences are permissive and
compatible with this repository's MIT licence for vendored evidence under
`docs/`, but the Apache-2.0 files carry attribution and notice obligations
that adapting them into `src/` would trigger; nothing here is adapted.

`in-toto-sign.py` was located through a corpus tree materialised from the PyPI
3.1.0 sdist, whose manifest records `parity: drift` — 58 files exist in git and
not in the sdist. The cited file is present in both, and the URL above resolves
at commit `c82fe5d2…`, which is tag `v3.1.0`.

Vendoring proves these bytes were obtained; it does not prove they came from
those URLs. Confirming provenance needs a second, independent fetch of the
cited URL, which the offline suite cannot perform.
