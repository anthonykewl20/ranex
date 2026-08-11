# Vendored prior art — ADR-019

Third-party source copied so that what ADR-019 claims to have read is on disk.
Each line below records the file, its licence, and the commit and URL the copy
was taken at. Nothing here is Ranex code and nothing here is modified: these are
the upstream bytes, and their `git hash-object` values are recorded beside the
citations in the ADR's `## Prior art` section.

This repository is MIT. Every licence below permits the copy, and the Apache-2.0
licence text required by section 4 of that licence travels with them — it is the
last entry in the list.

- `securesystemslib-dsse.py` — MIT, Copyright (c) 2016 Santiago Torres — `securesystemslib/dsse.py` from secure-systems-lab/securesystemslib at commit 47b0f4512fe974d6df75dbd4ad62c2642d4e5806 (v1.4.0), https://raw.githubusercontent.com/secure-systems-lab/securesystemslib/47b0f4512fe974d6df75dbd4ad62c2642d4e5806/securesystemslib/dsse.py
- `tuf-trusted-metadata-set.py` — MIT OR Apache-2.0 per its own SPDX header, taken under MIT, Copyright the TUF contributors — `tuf/ngclient/_internal/trusted_metadata_set.py` from theupdateframework/python-tuf at commit 353bdb767db56fd4667c9bcf56b710d50fdc2ac0 (v7.0.0), https://raw.githubusercontent.com/theupdateframework/python-tuf/353bdb767db56fd4667c9bcf56b710d50fdc2ac0/tuf/ngclient/_internal/trusted_metadata_set.py
- `kubelet-filestore.go` — Apache-2.0, Copyright 2017 The Kubernetes Authors — `pkg/kubelet/util/store/filestore.go` from kubernetes/kubernetes at commit a57b6f7709f6c2722b92f07b8b4c48210a51fc40 (v1.33.2), https://raw.githubusercontent.com/kubernetes/kubernetes/a57b6f7709f6c2722b92f07b8b4c48210a51fc40/pkg/kubelet/util/store/filestore.go
- `cosign-exit-code-lookup.go` — Apache-2.0, Copyright The Sigstore Authors — `cmd/cosign/errors/exit_code_lookup.go` from sigstore/cosign at commit 11926fa5bbbbde47e88fc006b625a17769b743b2 (v3.1.3), https://raw.githubusercontent.com/sigstore/cosign/11926fa5bbbbde47e88fc006b625a17769b743b2/cmd/cosign/errors/exit_code_lookup.go
- `LICENSE-APACHE-2.0.txt` — Apache-2.0, the licence text itself, required by section 4 to accompany the Apache-2.0 files above and offered as one option for the dual-licensed TUF file — `LICENSE` from sigstore/cosign at commit 11926fa5bbbbde47e88fc006b625a17769b743b2, https://raw.githubusercontent.com/sigstore/cosign/11926fa5bbbbde47e88fc006b625a17769b743b2/LICENSE

## What the vendored bytes prove, and what they do not

They prove these files were obtained, which catches the failure that actually
happens: citing an implementation from memory. They do **not** prove the bytes
came from the URLs above. Establishing that needs a second, independent fetch of
each cited URL, and the offline suite cannot do it. The recorded hash is git's
own, so a reviewer with a network can compare against the code host by eye.
