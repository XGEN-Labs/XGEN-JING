"""Duration and interaction budgets for generated stories."""

from typing import Any

from .actions import parse_timestamp


def limits(duration: float) -> tuple[int, int, int]:
    for seconds, actions, people, turns in (
        (15, 5, 2, 2),
        (24, 7, 3, 4),
        (30, 9, 3, 4),
        (50, 18, 3, 6),
        (60, 24, 4, 8),
    ):
        if duration <= seconds:
            return actions, people, turns
    return 24, 4, 8


def validate_document(data: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    agents = data.get("agents", {})
    actions = agents.get("ego", {}).get("action_list", {}).get("actions", [])
    if not isinstance(actions, list) or not actions:
        return ["actions must be a nonempty list"], warnings
    duration, turns = 0.0, 0
    for index, action in enumerate(actions, 1):
        if not isinstance(action, dict):
            errors.append(f"action {index} must be an object")
            continue
        try:
            _, duration = parse_timestamp(action.get("timestamp"))
        except ValueError:
            errors.append(f"action {index} has invalid timestamp")
        refs = action.get("dialogue_refs", [])
        if isinstance(refs, list):
            turns += len(refs)
            if len(refs) > 1:
                errors.append(f"action {index} contains more than one speaking turn")
    participants = 1 + len(agents.get("npcs", []))
    action_limit, participant_limit, turn_limit = limits(duration)
    if duration > 60:
        errors.append(f"duration {duration:.3f}s exceeds the 60s limit")
    if len(actions) > action_limit:
        warnings.append(f"{len(actions)} actions exceed advisory limit {action_limit}")
    if participants > participant_limit:
        errors.append(f"{participants} participants exceed limit {participant_limit}")
    if turns > turn_limit:
        errors.append(f"{turns} dialogue turns exceed limit {turn_limit}")
    if len(actions) < 3 and duration > 10:
        warnings.append("few actions for duration; check overloaded or static chunks")
    return errors, warnings
