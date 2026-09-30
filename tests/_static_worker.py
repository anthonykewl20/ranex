"""Measured, pinned static fixture builds using the production closure verifier."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

from ranex.cli.host_confinement import _pinned_inputs, _trace_inputs, _verify_observed_closure


def build_worker(root: Path, source: Path, output: Path, manifest: dict, *, trace: Path | None = None) -> bytes:
    build = manifest["build"]
    compiler = Path(build["compiler"]["path"])
    tracer = Path(build["observer"]["path"])
    assert hashlib.sha256(compiler.read_bytes()).hexdigest() == build["compiler"]["sha256"]
    assert hashlib.sha256(tracer.read_bytes()).hexdigest() == build["observer"]["sha256"]
    assert hashlib.sha256(source.read_bytes()).hexdigest() == build["source"]["sha256"]
    # Verify before invocation as well as against the observed read closure.
    pinned = _pinned_inputs(build)
    for item in pinned.values():
        assert hashlib.sha256(item.realpath.read_bytes()).hexdigest() == item.sha256
    flags = [token.replace("<ABS_REPO_ROOT>", str(root.resolve()))
             .replace("<output>", str(output)).replace("<source>", str(source))
             for token in build["flags"]]
    trace = trace or output.with_name(output.name + ".build.trace")
    result = subprocess.run(
        [str(tracer), "-f", "-qq", "-s", "4096", "-e", "trace=%file,%network",
         "-o", str(trace), str(compiler), *flags],
        cwd=root, env=build["environment"], capture_output=True, check=False,
    )
    assert result.returncode == 0, result.stderr.decode(errors="replace")
    observed, network = _trace_inputs(trace, root, output.parent, source)
    assert not network, "static fixture compilation attempted network access"
    _verify_observed_closure(observed, pinned, root)
    image = output.read_bytes()
    assert hashlib.sha256(image).hexdigest() == manifest["artifact"]["sha256"]
    return image
