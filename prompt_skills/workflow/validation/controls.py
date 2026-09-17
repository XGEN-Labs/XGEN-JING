"""Control strings shared by intermediate actions and final cases."""

import re

CONTROL_RE = re.compile(r"[wasd](?:,[wasd])*")


def validate_control(value, label, errors):
    if not isinstance(value, str) or (value != "" and not CONTROL_RE.fullmatch(value)):
        errors.append(
            f"{label}: use WASD keys such as 'w,a' or ''; legacy trajectory expressions are not supported"
        )


def action_controls(action):
    label = f"action {action.get('action_id')}"
    if "trajectory" in action:
        raise ValueError(
            f"{label}: legacy trajectory is not supported; regenerate with control lists"
        )
    controls = action.get("control")
    if not isinstance(controls, list) or not controls:
        raise ValueError(f"{label}: control must be a nonempty list")
    errors = []
    for index, value in enumerate(controls):
        validate_control(value, f"{label} control {index}", errors)
    if errors:
        raise ValueError("; ".join(errors))
    return controls


def has_translation(schedule):
    for value in schedule:
        if isinstance(value, str) and CONTROL_RE.fullmatch(value):
            keys = set(value.split(","))
            if ("w" in keys) != ("s" in keys) or ("a" in keys) != ("d" in keys):
                return True
    return False
