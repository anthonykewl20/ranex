"""Deterministic, closed-DSL projections of approved specification packets."""

from ranex.specification_generation.projection import (
    TRACE_PROJECTION_VERSION,
    ProjectionError,
    ProjectionResult,
    generate_projections,
    trace_projection_descriptor,
    trace_projection_digest,
    verify_projection,
)

__all__ = [
    "ProjectionError",
    "ProjectionResult",
    "TRACE_PROJECTION_VERSION",
    "generate_projections",
    "trace_projection_descriptor",
    "trace_projection_digest",
    "verify_projection",
]
