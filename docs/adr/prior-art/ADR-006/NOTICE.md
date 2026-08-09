# Third-party source vendored for ADR-006

These are verbatim upstream implementation evidence for review. Ranex does not
import, execute, adapt or relicense them. Git blob hashes in ADR-006 were checked
against the official repositories at the immutable revisions below; that binds
the bytes, while URL provenance still depends on the recorded fetch.

- `containerd-cgroup2-manager.go` — Apache-2.0 — containerd/cgroups `cgroup2/manager.go` at v3.1.3 commit `076b5e0e60bd073ead691caf95a90ac0f2fbec5d`, blob `38d7556598795fe37f5f13d9416a134124b33cf8`, from <https://github.com/containerd/cgroups/blob/076b5e0e60bd073ead691caf95a90ac0f2fbec5d/cgroup2/manager.go>; Copyright The containerd Authors, with Apache-2.0 terms retained in the file header.
- `containerd-cgroup2-manager-test.go` — Apache-2.0 — containerd/cgroups `cgroup2/manager_test.go` at v3.1.3 commit `076b5e0e60bd073ead691caf95a90ac0f2fbec5d`, blob `5ee6971c3b73c851e656f8bce19030fef119c807`, from <https://github.com/containerd/cgroups/blob/076b5e0e60bd073ead691caf95a90ac0f2fbec5d/cgroup2/manager_test.go>; Copyright The containerd Authors, with Apache-2.0 terms retained in the file header.
- `linux-landlock-sandboxer.c` — BSD-3-Clause — Linux `samples/landlock/sandboxer.c` at v7.1 commit `8cd9520d35a6c38db6567e97dd93b1f11f185dc6`, blob `66e56ae275c6b350cc0dedb4ef05aca5e1d4d8e3`, from <https://github.com/torvalds/linux/blob/8cd9520d35a6c38db6567e97dd93b1f11f185dc6/samples/landlock/sandboxer.c>; Copyright © 2017-2020 Mickaël Salaün and © 2020 ANSSI, with SPDX terms retained in the file.
- `landrun-sandbox.go` — MIT — landrun `internal/sandbox/sandbox.go` at v0.1.17 commit `62823c05e58ec22c1f91b4c8468318c1f97f2d32`, blob `2487567c1953ac17f0144c7ed6902d6cc2459be3`, from <https://github.com/Zouuup/landrun/blob/62823c05e58ec22c1f91b4c8468318c1f97f2d32/internal/sandbox/sandbox.go>; Copyright © 2025 Armin ranjbar.
- `go-landlock-restrict.go` — MIT — go-landlock `landlock/restrict.go` at v0.9.0 resolved commit `e573f52a61e3072813de11359239d2ccae9705d2`, blob `34755a18d12ba505bacd1cd8b58fceb629d9c5bf`, from <https://github.com/landlock-lsm/go-landlock/blob/e573f52a61e3072813de11359239d2ccae9705d2/landlock/restrict.go>; Copyright © 2021 Günther Noack.
- `py-landlock-landlock.py` — MIT — py-landlock `py_landlock/landlock.py` at v0.1.1 resolved commit `932af28940493fd6189d96a4b00c539a006c96c2`, blob `0a3e98c2cfab07eacdf9cfd4a10a5142a6516f76`, from <https://github.com/SebastienWae/py-landlock/blob/932af28940493fd6189d96a4b00c539a006c96c2/py_landlock/landlock.py>; Copyright © 2026.

Exact upstream licence and notice payloads accompany those source copies; the repository root licence is not used as a substitute:

- `LICENSE-CONTAINERD-APACHE-2.0.txt` — Apache-2.0 — exact containerd/cgroups `LICENSE` at `076b5e0e60bd073ead691caf95a90ac0f2fbec5d`, blob `261eeb9e9f8b2b4b0d119366dda99c6fd7d35c64`, from <https://github.com/containerd/cgroups/blob/076b5e0e60bd073ead691caf95a90ac0f2fbec5d/LICENSE>.
- `LICENSE-LINUX-BSD-3-Clause.txt` — BSD-3-Clause — exact Linux `LICENSES/preferred/BSD-3-Clause` at `8cd9520d35a6c38db6567e97dd93b1f11f185dc6`, blob `34c7f057c8d5441314c339ba574a9c6224ce0f80`, from <https://github.com/torvalds/linux/blob/8cd9520d35a6c38db6567e97dd93b1f11f185dc6/LICENSES/preferred/BSD-3-Clause>.
- `LICENSE-LANDRUN-MIT.txt` — MIT — exact landrun `LICENSE` at `62823c05e58ec22c1f91b4c8468318c1f97f2d32`, blob `7efcb24904d270788935e4c6c7e36b95f871667c`, from <https://github.com/Zouuup/landrun/blob/62823c05e58ec22c1f91b4c8468318c1f97f2d32/LICENSE>.
- `LICENSE-GO-LANDLOCK-MIT.txt` — MIT — exact go-landlock `LICENSE` at `e573f52a61e3072813de11359239d2ccae9705d2`, blob `aaa7810eb0d5112bd55d69d28f58fd54dad51148`, from <https://github.com/landlock-lsm/go-landlock/blob/e573f52a61e3072813de11359239d2ccae9705d2/LICENSE>.
- `LICENSE-PY-LANDLOCK-MIT.txt` — MIT — exact py-landlock `LICENSE` at `932af28940493fd6189d96a4b00c539a006c96c2`, blob `14fac913ccf80234b1848540089a3bbcb6e5283d`, from <https://github.com/SebastienWae/py-landlock/blob/932af28940493fd6189d96a4b00c539a006c96c2/LICENSE>.

The containerd files remain Apache-2.0, the Linux sample remains BSD-3-Clause,
and the landrun, go-landlock and py-landlock files remain MIT.
Their upstream copyright, licence and notice obligations remain in force; this
repository does not relicense them.

Deliberately not copied:

- OpenAI Codex informed discussion, but the focused Rust excerpts previously
  copied here were not complete upstream source files. They and their Apache
  licence/NOTICE payloads were removed and are not adopted evidence.
- Bubblewrap's C implementation is LGPL-2.0-or-later. The decision uses a pinned
  installed executable and does not copy Bubblewrap source.
- Linux Landlock selftests are GPL-2.0-only. The BSD-3-Clause canonical sample
  supplies the copied syscall evidence; selftests are discussion-only.
- CPython v3.14.6 `run_workers.py` and `_posixsubprocess.c` do not prove complete
  descendant cleanup; SLSA workflows demonstrate conceptual signer separation,
  not a runtime worker boundary.
- Nix/systemd cgroup launchers are LGPL and were not copied. The permissive
  containerd manager and tests are copied, but their fallback semantics are
  expressly rejected; Ranex's lifecycle must qualify in SLICE-018 and reach
  production only through SLICE-019.
- gVisor OCI launch code is UNVERIFIED. No gVisor source is copied or adopted;
  the optional profile remains unavailable until separate research and tests.
