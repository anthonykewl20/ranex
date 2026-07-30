# Spec Kit selective-adaptation review prompt

Both complete independent reviews received the following prompt and the same
attached source bytes:

> Perform a read-only, independent architecture and product-fit review. Subject:
> whether Ranex should selectively adapt proven patterns from github/spec-kit
> pinned at commit f36634b5c1463d3592382e863cd5e7b8a94d9c9a. Do not treat
> GitHub stars or popularity as proof of correctness or production fitness; they
> are adoption signals only. Do not see or assume another reviewer verdict. Use
> only the attached upstream and Ranex documents. Evaluate every relevant Spec
> Kit surface: constitution, specify, clarify, plan, tasks, checklist, analyze,
> implement, converge, taskstoissues, artifact evolution, integrations,
> extensions, presets, workflows, bundles, catalog/provenance, and
> greenfield/brownfield use. Produce: (1) verdict on selective adoption; (2) an
> ADOPT/MODIFY/REJECT/DEFER matrix with exact evidence citations, Ranex fit, user
> value, differentiation/moat, implementation effort, and governance/security
> risks; (3) the smallest first end-to-end slice; (4) patterns that conflict
> with Ranex invariants; (5) commercial-value hypotheses clearly separated from
> facts; (6) unresolved questions and required RFC/ADR decisions. Favor
> Ranex-native semantics over copying names or files. Do not edit files and do
> not attempt to read unprovided paths.

HY3 stopped after item 5. It received this continuation without any new source
or other review:

> Your independent review answered items 1 through 5 but stopped before item 6.
> Without revising the earlier verdict and without reading any new sources or
> another reviewer, complete only: (6) unresolved questions and the exact
> RFC/ADR decisions required before any adaptation. Also list any claim in your
> earlier answer that you regard as uncertain because it was not directly
> supported by the attached subject. Do not edit files.
