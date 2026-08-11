# Vendored prior art — ADR-020

Third-party source copied so that what ADR-020 claims to have read is on disk.
Each line below records the file, its licence, and the commit and URL the copy
was taken at. Nothing here is Ranex code and nothing here is modified: these are
the upstream bytes, and their `git hash-object` values are recorded beside the
citations in the ADR's `## Prior art` section.

This repository is MIT. Every file below is Apache-2.0, which permits the copy
with attribution, and the licence text that section 4 requires to accompany them
is the last entry in the list.

- `kyverno-rulestatus.go` — Apache-2.0, Copyright The Kyverno Authors — `pkg/engine/api/rulestatus.go` from kyverno/kyverno at commit 945ac9ce8546ea6cd51370f24b615148c577da5e (v1.18.2), https://raw.githubusercontent.com/kyverno/kyverno/945ac9ce8546ea6cd51370f24b615148c577da5e/pkg/engine/api/rulestatus.go
- `kyverno-cli-result.go` — Apache-2.0, Copyright The Kyverno Authors — `cmd/cli/kubectl-kyverno/processor/result.go` from kyverno/kyverno at commit 945ac9ce8546ea6cd51370f24b615148c577da5e (v1.18.2), https://raw.githubusercontent.com/kyverno/kyverno/945ac9ce8546ea6cd51370f24b615148c577da5e/cmd/cli/kubectl-kyverno/processor/result.go
- `k8s-apimachinery-errors.go` — Apache-2.0, Copyright The Kubernetes Authors — `staging/src/k8s.io/apimachinery/pkg/api/errors/errors.go` from kubernetes/kubernetes at commit 0f29094e5b73085e3802ecc1298ecae13866bfe6 (v1.36.3), https://raw.githubusercontent.com/kubernetes/kubernetes/0f29094e5b73085e3802ecc1298ecae13866bfe6/staging/src/k8s.io/apimachinery/pkg/api/errors/errors.go
- `knative-condition-set.go` — Apache-2.0, Copyright The Knative Authors — `apis/condition_set.go` from knative/pkg at commit 39ebae2ee2dc245299eb6a3b12034fb624b86156, the revision pinned by tektoncd/pipeline v1.15.0's go.mod because knative/pkg publishes no release tags, https://raw.githubusercontent.com/knative/pkg/39ebae2ee2dc245299eb6a3b12034fb624b86156/apis/condition_set.go
- `LICENSE-APACHE-2.0.txt` — Apache-2.0, the licence text itself, required by section 4 to accompany the four files above — `LICENSE` from sigstore/cosign at commit 11926fa5bbbbde47e88fc006b625a17769b743b2, https://raw.githubusercontent.com/sigstore/cosign/11926fa5bbbbde47e88fc006b625a17769b743b2/LICENSE

## What the vendored bytes prove, and what they do not

They prove these files were obtained, which catches the failure that actually
happens: citing an implementation from memory. They do **not** prove the bytes
came from the URLs above. Establishing that needs a second, independent fetch of
each cited URL, and the offline suite cannot do it. The recorded hash is git's
own, so a reviewer with a network can compare against the code host by eye.
