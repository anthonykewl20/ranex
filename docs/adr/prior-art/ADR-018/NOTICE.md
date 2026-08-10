# Third-party notices for ADR-018

Each file is third-party source copied unmodified at a pinned immutable commit,
resolved from a dotted-numeric release tag. `blob:` values are recorded in the
ADR's `Vendored:` lines and enforced by `tests/contract/test_docs_discipline.py`.

- `k9s-view-table.go`: k9s `internal/view/table.go` at commit 558caafe7ba067467de46b320cc22ef11fef9c34 (tag v0.51.0); SPDX-License-Identifier: Apache-2.0; `// Copyright Authors of K9s`; licence text in LICENSE-K9S-APACHE-2.0.txt.
- `trivy-report-table.go`: Trivy `pkg/report/table/table.go` at commit 40c73e5d6166dcc0346a1ab4e94499d1572854e4 (tag v0.73.0); SPDX-License-Identifier: Apache-2.0; Copyright Aqua Security Software Ltd.; licence text in LICENSE-TRIVY-APACHE-2.0.txt.
- `textual-design.py`: Textual `src/textual/design.py` at commit 1d99508b928a771b51e1a527319c6b87dcff9e05 (tag v8.2.8); SPDX-License-Identifier: MIT; Copyright (c) 2021 Will McGugan.
- `lipgloss-color.go`: Lip Gloss `color.go` at commit 5bd778d050f0a5a130e7cf041917927496dbe722 (tag v2.0.5); SPDX-License-Identifier: MIT; Copyright (c) 2021-2026 Charmbracelet, Inc.
- `lazygit-layout.go`: lazygit `pkg/gui/layout.go` at commit aee0e40ec1235476e9328678f0f3e2462576b9ae (tag v0.64.0); SPDX-License-Identifier: MIT; Copyright (c) 2018 Jesse Duffield.
- `LICENSE-K9S-APACHE-2.0.txt`: the k9s repository `LICENSE` at commit 558caafe7ba067467de46b320cc22ef11fef9c34; SPDX-License-Identifier: Apache-2.0; carried because Apache-2.0 requires the licence to travel with the copy.
- `LICENSE-TRIVY-APACHE-2.0.txt`: the Trivy repository `LICENSE` at commit 40c73e5d6166dcc0346a1ab4e94499d1572854e4; SPDX-License-Identifier: Apache-2.0; carried because Apache-2.0 requires the licence to travel with the copy.

Only `k9s-view-table.go` carries an SPDX header inline. For the other four the
licence is the repository's, established by fetching its root licence file
rather than read off the vendored bytes.

## Licence compatibility

This repository is MIT. MIT and Apache-2.0 are both permissive and both may be
copied in, provided attribution travels with the copy — that is this file, plus
the two Apache texts. No copyleft source is vendored here and none may be.

`open-policy-agent/conftest` was the closest domain match for verdict rendering
and was rejected on licence grounds: GitHub resolves its licence as
`NOASSERTION`, so no machine-readable licence could be established. Trivy was
cited instead.

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

These five sources were fetched at the pinned commits and their local git blob
hashes match the vendored bytes. That proves the bytes are present; it does not
prove they came from the recorded URL, which needs a second fetch the offline
suite cannot perform.
