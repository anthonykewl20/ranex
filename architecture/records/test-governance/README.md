# Test-governance governed records

This root contains closed canonical JSON authority sources. Its live initial
population is empty.

ADR-0010 currently admits only:

- `behavior-authorities/<behavior_id>@<behavior_version>.json`

Files at this root, unexpected child paths, symlinks, templates, and fixtures
are not authority. See the child README and ADR-0010 for the exact source,
catalog, lifecycle, landing, and sealing requirements.
