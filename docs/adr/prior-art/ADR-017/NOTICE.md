# Third-party notices for ADR-017

- `spec-kit-workflow.yml`: GitHub Spec Kit `workflows/speckit/workflow.yml` at commit `684b3d8e05263a7c1948d3d0699ab1cb4f77c3d5`; SPDX-License-Identifier: MIT.
  Copyright GitHub, Inc. The vendored file itself carries no SPDX header or
  copyright line (only `author: GitHub`); the MIT licence is the repository's,
  confirmed by fetch rather than read from the file.
- `openspec-artifact-state.ts`: OpenSpec `src/core/artifact-graph/state.ts` at commit `e50bd0983dc8dc48250e3181f36e28450542f2ab`; SPDX-License-Identifier: MIT.
  Copyright (c) 2024 OpenSpec Contributors.
- `xstate-adjacency.ts`: XState `packages/core/src/graph/adjacency.ts` at commit `c25dba07a2b68565edbe83d83c5d679dd85e00b2`; SPDX-License-Identifier: MIT.
  Copyright (c) 2015 David Khourshid.
- `arxic-evidence-ref.ts`: Arxic `packages/contracts/src/evidence-ref.ts` at commit `135991d9b1a07c2ffa08e38f8e261543ec5ab980`; SPDX-License-Identifier: MIT. Note: `anthonykewl20/arxic` is a first-party, private repository under the same owner as this one; its provenance is therefore not third-party verifiable by re-fetch, unlike the three public sources above.
  Copyright (c) 2026 Arxic maintainers and contributors.

## MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Provenance caveat

The four sources above were fetched at the pinned immutable commits. Local git
blob hashes match the vendored bytes (enforced by tests/contract/test_docs_discipline.py);
proving the bytes came from the recorded URL needs a second fetch. The Arxic
repository is private and first-party, so its citation is permanently unverifiable
by any third party — a stated limit on this evidence.
