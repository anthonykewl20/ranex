# Third-party notices for ADR-022

Each file is third-party source copied unmodified at a pinned immutable commit,
resolved from a dotted-numeric release tag. `blob:` values are recorded in the
ADR's `Vendored:` lines and enforced by `tests/contract/test_docs_discipline.py`.

- `cliui-table.ts`: `poppinss/cliui` `src/table.ts` at commit 319531c0be1946072e7da29ea45f4514939aff06 (tag v6.8.1); SPDX-License-Identifier: MIT; Copyright 2021 Harminder Virk, contributors.
- `glamour-codeblock.go`: `charmbracelet/glamour` `ansi/codeblock.go` at commit 05ee9b5f4dcf3e4426c4ba41e1f9d7ea4f34d603 (tag v0.10.0, dereferenced from its annotated tag object); SPDX-License-Identifier: MIT; Copyright (c) 2019-2023 Charmbracelet, Inc.

Neither file carries an SPDX header inline. For both, the licence is the
repository's, established by fetching its root licence file — `LICENSE.md` for
cliui and `LICENSE` for glamour — and reading it, rather than read off the
vendored bytes.

`cliui-table.ts` here is byte-identical to the copy already vendored in the
harness repository at `specs/tui-redesign/references/cliui-table.ts`
(blob `a312cc77c588b5bcf266f97ed3093863cc956615` in both). That is a
cross-check, not a duplication: the two repositories are distributed
separately, so each carries its own attribution.

## Licence compatibility

This repository is MIT. Both sources above are MIT, which may be copied in
provided attribution travels with the copy — that is this file plus the licence
text below. No copyleft source is vendored here and none may be.

`alecthomas/chroma` was the other candidate for the syntax-highlighting citation
and was not vendored: glamour is the layer that actually decides how a document
theme reaches the highlighter, which is the decision this ADR makes, and citing
the lexer below it would have named a dependency rather than the design.

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
