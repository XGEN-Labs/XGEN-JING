"""Validation shared by the generation stages and compiler."""

from ..common import WorkflowError


def check(errors: list[str], warnings: list[str], label: str) -> None:
    for warning in warnings:
        print(f"WARN {label}: {warning}")
    if errors:
        raise WorkflowError(f"{label}: " + "; ".join(errors))
