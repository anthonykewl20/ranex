"""Unit arms for acceptance-task profile and miss accounting helpers."""
from __future__ import annotations

import pytest

from ranex.cli.acceptance_task import module_digest, refuse, require, worker_profile

PG = "sha256:e013e867e712fec275706a6c51c966f0bb0c93cfa8f51000f85a15f9865a28cb"


def test_module_digest_is_sha256_of_controller_bytes() -> None:
    digest = module_digest()
    assert digest.startswith("sha256:")
    assert len(digest) == 71


def test_require_and_refuse_prefix_task_errors() -> None:
    with pytest.raises(ValueError, match="^E-TASK-ABSENT"):
        refuse("ABSENT: missing")
    require(True, "never")
    with pytest.raises(ValueError, match="^E-TASK-REVOKED"):
        require(False, "REVOKED: three misses")


def test_worker_profile_closed_shape() -> None:
    profile = dict(
        version="docker-worker-v1",
        image=PG,
        argv=["/bin/true", "arg"],
        product_roots=["product"],
        timeout_seconds=30,
        network=False,
        environment=["TOKEN"],
    )
    assert worker_profile(profile, ["acceptance"])["argv"][0] == "/bin/true"
    for change in (
        {"version": "other"},
        {"image": "sha256:dead"},
        {"argv": ["relative"]},
        {"timeout_seconds": 0},
        {"network": "yes"},
        {"environment": ["token"]},
        {"product_roots": ["acceptance"]},
    ):
        bad = {**profile, **change}
        with pytest.raises(ValueError, match="E-TASK-"):
            worker_profile(bad, ["acceptance"])
