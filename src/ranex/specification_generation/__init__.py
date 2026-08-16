"""Deterministic, closed-DSL projections of approved specification packets."""

from ranex.specification_generation.projection import (
    ProjectionError,
    ProjectionResult,
    generate_projections,
    verify_projection,
)

__all__ = ["ProjectionError", "ProjectionResult", "generate_projections", "verify_projection"]
