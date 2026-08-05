# Vendored prior art for ADR-011

Copied verbatim for review. No file here is imported, executed, or adapted
into this tree; they are evidence that the cited implementations were read.

| File | Origin | Licence |
|---|---|---|
| `cpython_results.py` | <https://raw.githubusercontent.com/python/cpython/37e98da7c19a9e5892ee756d6dee08225422cd49/Lib/test/libregrtest/results.py> | PSF-2.0 (BSD-style permissive; per Python's LICENSE file) |
| `SkippedThreshold.java` | <https://raw.githubusercontent.com/jenkinsci/xunit-plugin/xunit-3.1.7/src/main/java/org/jenkinsci/plugins/xunit/threshold/SkippedThreshold.java> | MIT |
| `mtest.py` | <https://raw.githubusercontent.com/mesonbuild/meson/1.5.1/mesonbuild/mtest.py> | Apache-2.0 |
| `pytest_error_for_skips.py` | <https://raw.githubusercontent.com/jankatins/pytest-error-for-skips/4c3eaae64e09dc077a52e219c3cf375e3e5dbdc0/pytest_error_for_skips.py> | MIT |

`cpython_results.py`'s Python Software Foundation License 2.0 is not
identical to BSD-3-Clause, but is described by Wikipedia and OSI as a
BSD-style, permissive, non-copyleft license — SPDX identifier `PSF-2.0`
(<https://spdx.org/licenses/PSF-2.0.html>).

`SkippedThreshold.java`'s MIT grant is declared in the `xunit-plugin`
repository's `pom.xml` `<licenses>` block and the file's own header comment;
the repository carries no top-level `LICENSE` file, which is the Jenkins-plugin
convention.

Vendoring proves these bytes were obtained; it does not prove they came from
those URLs. Confirming provenance needs a second, independent fetch of the
cited URL, which the offline suite cannot perform.
