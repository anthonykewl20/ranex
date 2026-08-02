# Third-party source vendored for ADR-004

Copies of upstream implementations, kept so that what ADR-004 claims to have read
is on disk and checkable. They are evidence, not dependencies: nothing imports,
executes or lints them.

Each was fetched at the pinned revision named below, and its git blob hash was
then compared against the hash GitHub reports for that path at that revision, so
these copies agree with upstream and not merely with each other.

- `openssh-session.c` — BSD-2-Clause — OpenSSH `session.c` at commit 53a80baaebda180f46e6e8571f3ff800e1f5c496 (release V_9_9_P1), blob `c9415114db94f2b7bd6ea483665f53d7b36a6d87`, from <https://github.com/openssh/openssh-portable/blob/53a80baaebda180f46e6e8571f3ff800e1f5c496/session.c> — Copyright (c) 1995 Tatu Ylonen; SSH2 support Copyright (c) 2000, 2001 Markus Friedl, under the two-clause BSD terms carried in the file header.
- `sudo-env.c` — ISC — sudo `plugins/sudoers/env.c` at commit c1a6140608d591b6992c6f8674ee2ce684a0481a (release SUDO_1_9_16), blob `95558e9edfa457f5b3a8e5665f5d80e3d21f59ce`, from <https://github.com/sudo-project/sudo/blob/c1a6140608d591b6992c6f8674ee2ce684a0481a/plugins/sudoers/env.c> — Copyright (c) 2000-2005, 2007-2023 Todd C. Miller; the file carries `SPDX-License-Identifier: ISC`.

Both licences are permissive and compatible with this repository's MIT licence,
and both require the copyright notice to travel with the copy — which is what
this file is for.

Deliberately absent: git's own `prepare_other_repo_env` and `local_repo_env`,
which solve this problem more directly than either file above. git is
GPL-2.0-only, and copying it into an MIT repository would change what this
repository may be distributed under. It is discussed in ADR-004 and not
vendored. That is the licence rule doing its job rather than a gap.
