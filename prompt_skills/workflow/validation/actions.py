"""Validate generated actions, timing, dialogue and controls."""

from __future__ import annotations

import json
import math
import re
from typing import Any

from .controls import action_controls, has_translation
from .entities import is_physical_identifier

HASH_RE = re.compile(r"^[0-9a-f]{64}$")
DISALLOWED_RE = re.compile(
    r"<\s*/?\s*d\b[^>]*>|\[(?:Chinese|English)\]|"
    r"integrated_multimodal_description|overall_soundscape:|non_diegetic_music:",
    re.IGNORECASE,
)
NUMBERED_ENTITY_RE = re.compile(r"(?<![A-Za-z0-9_])(?:S\d+|O\d+|B\d+)(?![A-Za-z0-9_])")
CHINESE_QUOTE_RE = re.compile(r"“([^”]+)”")
ASCII_QUOTE_RE = re.compile(r'"([^"]+)"')
DISCONTINUITY_RE = re.compile(
    r"画面切到|镜头切到|跳切|硬切|瞬移|镜头(?:重置|复位)|"
    r"authored[_ -]?cut|jump\s+cut|hard\s+cut|cut\s+to|"
    r"teleport(?:s|ed|ing|ation)?|camera\s+reset|scene\s+reset",
    re.IGNORECASE,
)
NEGATION_RE = re.compile(
    r"(?:不|无|没有|禁止|避免|不可|不得|严禁)\s*$|"
    r"(?:no|not|never|without|forbid(?:s|den)?|avoid(?:s|ed|ing)?)\s+(?:any\s+)?$",
    re.IGNORECASE,
)
PHYSICAL_BRIDGE_RE = re.compile(
    r"走|移动|穿过|通过|进入|离开|沿|跨过|绕过|上楼|下楼|"
    r"门|门槛|走廊|通道|路径|小路|楼梯|拐角|"
    r"\b(?:walk|move|travel|cross|enter|leave|exit|follow|door|threshold|"
    r"corridor|passage|path|stairs|corner)\b",
    re.IGNORECASE,
)


def has_numbered_entity_label(text: str, context: str = "") -> bool:
    return any(
        not is_physical_identifier(text, match, context)
        for match in NUMBERED_ENTITY_RE.finditer(text)
    )


def is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def has_unnegated_discontinuity(value: str) -> bool:
    for match in DISCONTINUITY_RE.finditer(value):
        left_context = value[max(0, match.start() - 32) : match.start()]
        if not NEGATION_RE.search(left_context):
            return True
    return False


def parse_timecode(value: str) -> float:
    parts = value.strip().split(":")
    if len(parts) not in (2, 3):
        raise ValueError("timecode must be MM:SS.s or HH:MM:SS.s")
    numbers = [float(part) for part in parts]
    if any(number < 0 for number in numbers):
        raise ValueError("negative time component")
    if len(numbers) == 2:
        minutes, seconds = numbers
        if seconds >= 60:
            raise ValueError("seconds must be below 60")
        return minutes * 60 + seconds
    hours, minutes, seconds = numbers
    if minutes >= 60 or seconds >= 60:
        raise ValueError("minutes and seconds must be below 60")
    return hours * 3600 + minutes * 60 + seconds


def parse_timestamp(value: str) -> tuple[float, float]:
    if not isinstance(value, str) or value.count("-") != 1:
        raise ValueError("timestamp must contain one start-end separator")
    start_text, end_text = value.split("-", 1)
    start, end = parse_timecode(start_text), parse_timecode(end_text)
    if end <= start:
        raise ValueError("timestamp end must be greater than start")
    return start, end


def nearest_repeat_budget(seconds: float, fps: float) -> int:
    return max(1, math.floor(((fps * seconds - 5.0) / 17.0) + 0.5))


def allocate_repeats(durations: list[float], total: int) -> list[int]:
    if total < len(durations):
        raise ValueError("repeat budget cannot give every action one repeat")
    raw = [duration / sum(durations) * total for duration in durations]
    values = [max(1, math.floor(value)) for value in raw]
    while sum(values) < total:
        index = max(
            range(len(values)), key=lambda i: (raw[i] - values[i], durations[i])
        )
        values[index] += 1
    while sum(values) > total:
        candidates = [index for index, value in enumerate(values) if value > 1]
        if not candidates:
            raise ValueError("unable to reduce repeat allocation")
        index = max(candidates, key=lambda i: (values[i] - raw[i], -durations[i]))
        values[index] -= 1
    return values


def expected_action_repeats(actions: list[dict[str, Any]], fps: float) -> list[int]:
    boundaries = [parse_timestamp(action["timestamp"]) for action in actions]
    durations = [end - start for start, end in boundaries]
    return allocate_repeats(durations, nearest_repeat_budget(boundaries[-1][1], fps))


def extract_utterances(text: str) -> list[str]:
    return [
        value.strip()
        for value in CHINESE_QUOTE_RE.findall(text) + ASCII_QUOTE_RE.findall(text)
        if value.strip()
    ]


def validate_environment(data: Any, label: str) -> tuple[set[str], list[str]]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return set(), [f"{label}: top level must be an object"]
    pipeline = data.get("_pipeline")
    if (
        not isinstance(pipeline, dict)
        or pipeline.get("schema_version") != "6.7"
        or pipeline.get("stage") != 2
    ):
        errors.append(f"{label}: environment pipeline metadata must match schema 6.7")
    elif not HASH_RE.fullmatch(str(pipeline.get("story_decision_sha256", ""))):
        errors.append(f"{label}: invalid story_decision_sha256")
    environments = data.get("environments")
    if not isinstance(environments, list) or not environments:
        return set(), errors + [f"{label}: environments must be nonempty"]
    ids: set[str] = set()
    for index, environment in enumerate(environments):
        item_label = f"{label}: environment {index}"
        if not isinstance(environment, dict):
            errors.append(f"{item_label}: must be an object")
            continue
        environment_id = environment.get("environment_id")
        if not nonempty(environment_id):
            errors.append(f"{item_label}: environment_id is required")
        elif environment_id in ids:
            errors.append(f"{item_label}: duplicate environment_id")
        else:
            ids.add(environment_id)
        if not nonempty(environment.get("content")):
            errors.append(f"{item_label}: content is required")
    return ids, errors


def validate_render_config(render: Any, label: str, errors: list[str]) -> None:
    if not isinstance(render, dict):
        errors.append(f"{label}: render_config must be an object")
        return
    if not nonempty(render.get("save_name")) or not render["save_name"].endswith(
        ".mp4"
    ):
        errors.append(f"{label}: render_config.save_name must end in .mp4")
    for field in ("seed", "height", "width", "num_inference_steps"):
        if not is_int(render.get(field)) or render[field] <= 0:
            errors.append(f"{label}: render_config.{field} must be a positive integer")
    fps = render.get("fps")
    if not isinstance(fps, (int, float)) or isinstance(fps, bool) or fps <= 0:
        errors.append(f"{label}: render_config.fps must be positive")
    for field in ("visual_style", "non_diegetic_music"):
        if not nonempty(render.get(field)):
            errors.append(f"{label}: render_config.{field} is required")
    if render.get("control_signal") != "camera_delta":
        errors.append(f"{label}: render_config.control_signal must be camera_delta")
    if render.get("prompt_language") not in ("Chinese", "English"):
        errors.append(
            f"{label}: render_config.prompt_language must be Chinese or English"
        )
    if render.get("discrete_camera") is not True:
        errors.append(f"{label}: render_config.discrete_camera must be true")


def validate_document(
    data: Any,
    label: str,
    environment_ids: set[str] | None = None,
) -> tuple[list[str], list[str], list[dict[str, Any]]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(data, dict):
        return [f"{label}: top level must be an object"], warnings, []

    identifier_context = json.dumps(data, ensure_ascii=False)
    pipeline = data.get("_pipeline")
    if (
        not isinstance(pipeline, dict)
        or pipeline.get("schema_version") != "6.7"
        or pipeline.get("stage") != 2
    ):
        errors.append(f"{label}: Action pipeline metadata must match schema 6.7")
    else:
        for field in ("story_decision_sha256", "environment_sha256"):
            if not HASH_RE.fullmatch(str(pipeline.get(field, ""))):
                errors.append(f"{label}: invalid _pipeline.{field}")

    validate_render_config(data.get("render_config"), label, errors)
    render = (
        data.get("render_config") if isinstance(data.get("render_config"), dict) else {}
    )
    language = render.get("prompt_language")

    intent = data.get("intent")
    if not isinstance(intent, dict):
        errors.append(f"{label}: intent must be an object")
        intent = {}
    if not nonempty(intent.get("goal")):
        errors.append(f"{label}: intent.goal is required")
    if not isinstance(intent.get("scene_change"), bool):
        errors.append(f"{label}: intent.scene_change must be boolean")
    start_id, end_id = (
        intent.get("start_environment_id"),
        intent.get("end_environment_id"),
    )
    for field, value in (
        ("start_environment_id", start_id),
        ("end_environment_id", end_id),
    ):
        if not nonempty(value):
            errors.append(f"{label}: intent.{field} is required")
        elif environment_ids is not None and value not in environment_ids:
            errors.append(f"{label}: intent.{field} is absent from Environment")
    if (
        isinstance(intent.get("scene_change"), bool)
        and nonempty(start_id)
        and nonempty(end_id)
    ):
        if intent["scene_change"] != (start_id != end_id):
            errors.append(
                f"{label}: intent.scene_change conflicts with environment IDs"
            )

    root_action = data.get("action")
    if not isinstance(root_action, dict):
        errors.append(f"{label}: action must be an object")
        root_action = {}
    if not nonempty(root_action.get("instruction")):
        errors.append(f"{label}: action.instruction is required")
    dialogues = root_action.get("supporting_dialogue")
    if not isinstance(dialogues, list) or any(
        not nonempty(value) for value in dialogues
    ):
        errors.append(
            f"{label}: action.supporting_dialogue must be an array of strings"
        )
        dialogues = []

    agents = data.get("agents")
    if not isinstance(agents, dict):
        errors.append(f"{label}: agents must be an object")
        agents = {}
    npcs = agents.get("npcs")
    if not isinstance(npcs, list):
        errors.append(f"{label}: agents.npcs must be an array")
        npcs = []
    agent_ids: set[str] = set()
    prompt_references: set[str] = set()
    agent_records: dict[str, dict[str, Any]] = {}
    for index, npc in enumerate(npcs):
        item = f"{label}: npc {index}"
        if not isinstance(npc, dict):
            errors.append(f"{item}: must be an object")
            continue
        agent_id = npc.get("agent_id")
        if not nonempty(agent_id) or agent_id in agent_ids:
            errors.append(f"{item}: agent_id must be nonempty and unique")
        else:
            agent_ids.add(agent_id)
            agent_records[agent_id] = npc
        for field in (
            "identity",
            "prompt_reference",
            "voice",
            "interaction_mode",
            "state_description",
        ):
            if not nonempty(npc.get(field)):
                errors.append(f"{item}: {field} is required")
        if "control" in npc or "trajectory" in npc:
            errors.append(
                f"{item}: control is forbidden for NPCs; it describes only the Ego/S1 first-person camera"
            )
        reference = npc.get("prompt_reference")
        if nonempty(reference):
            if reference in prompt_references:
                errors.append(f"{item}: prompt_reference must be unique")
            prompt_references.add(reference)
            if has_numbered_entity_label(reference, identifier_context):
                errors.append(f"{item}: prompt_reference may not contain S/O/B labels")

    ego = agents.get("ego")
    if not isinstance(ego, dict):
        errors.append(f"{label}: agents.ego must be an object")
        ego = {}
    ego_id = ego.get("agent_id")
    if not nonempty(ego_id) or ego_id in agent_ids:
        errors.append(f"{label}: ego agent_id must be nonempty and unique")
    else:
        agent_ids.add(ego_id)
        agent_records[ego_id] = ego
    for field in ("identity", "prompt_reference", "voice"):
        if not nonempty(ego.get(field)):
            errors.append(f"{label}: ego.{field} is required")

    action_list = ego.get("action_list")
    if not isinstance(action_list, dict):
        errors.append(f"{label}: ego.action_list must be an object")
        action_list = {}
    actions = action_list.get("actions")
    if not isinstance(actions, list) or not actions:
        errors.append(f"{label}: action_list.actions must be nonempty")
        actions = []
    if not is_int(action_list.get("total_num")) or action_list.get("total_num") != len(
        actions
    ):
        errors.append(f"{label}: action_list.total_num must equal action count")

    previous_end: float | None = None
    valid_actions: list[dict[str, Any]] = []
    control_schedules: list[list[Any] | None] = []
    previous_environment_id: str | None = None
    for index, current in enumerate(actions, start=1):
        item = f"{label}: action {index}"
        if not isinstance(current, dict):
            errors.append(f"{item}: must be an object")
            continue
        valid_actions.append(current)
        if current.get("action_id") != index:
            errors.append(f"{item}: action_id must equal {index}")
        try:
            start, end = parse_timestamp(current.get("timestamp"))
            if index == 1 and abs(start) > 0.05:
                errors.append(f"{item}: first action must start at zero")
            if previous_end is not None and abs(start - previous_end) > 0.05:
                errors.append(f"{item}: timestamp is not continuous")
            previous_end = end
        except Exception as exc:
            errors.append(f"{item}: invalid timestamp: {exc}")
        if current.get("action_type") not in ("navigation", "manipulation"):
            errors.append(f"{item}: invalid action_type")
        if not nonempty(current.get("action_plan")):
            errors.append(f"{item}: action_plan is required")

        try:
            control = action_controls(current)
        except ValueError as exc:
            errors.append(f"{item}: {exc}")
            control = None
        control_schedules.append(control)
        if control is not None and len(set(control)) != 1:
            errors.append(
                f"{item}: mixed control phases are forbidden; split translation "
                "and settle phases into separate actions with distinct prompts"
            )

        refs = current.get("dialogue_refs")
        if not isinstance(refs, list) or len(refs) > 1:
            errors.append(f"{item}: dialogue_refs must contain at most one line")
            refs = []
        elif any(value not in dialogues for value in refs):
            errors.append(f"{item}: dialogue_refs must exactly match root dialogue")
        speaker_id = current.get("speaker_agent_id")
        if refs:
            if speaker_id not in agent_ids:
                errors.append(f"{item}: speaker_agent_id must name a declared agent")
        elif speaker_id is not None:
            errors.append(f"{item}: speaker_agent_id must be null without dialogue")

        dynamics = current.get("scene_dynamics")
        if not isinstance(dynamics, list) or not dynamics:
            errors.append(f"{item}: scene_dynamics must be nonempty")
            dynamics = []
        current_environment_ids: list[str] = []
        for dynamic_index, dynamic in enumerate(dynamics):
            dlabel = f"{item} dynamic {dynamic_index}"
            if not isinstance(dynamic, dict):
                errors.append(f"{dlabel}: must be an object")
                continue
            environment_id = dynamic.get("environment_id")
            description = dynamic.get("description")
            if not nonempty(environment_id):
                errors.append(f"{dlabel}: environment_id is required")
            elif environment_ids is not None and environment_id not in environment_ids:
                errors.append(f"{dlabel}: environment_id is absent from Environment")
            else:
                current_environment_ids.append(environment_id)
            if not nonempty(description) or (
                nonempty(environment_id) and environment_id not in description
            ):
                errors.append(f"{dlabel}: description must name its environment_id")
            elif has_unnegated_discontinuity(description):
                errors.append(
                    f"{dlabel}: discontinuity language is forbidden; connect environments "
                    "through visible first-person physical movement"
                )

        description = current.get("action_description")
        if not nonempty(description):
            errors.append(f"{item}: action_description is required")
            continue
        valid_opening = True
        if language == "Chinese":
            valid_opening = description.startswith("第一人称POV")
        elif language == "English":
            valid_opening = bool(re.match(r"^First-person POV(?:\.|\s)", description))
        if not valid_opening:
            errors.append(
                f"{item}: action_description opening conflicts with prompt_language"
            )
        if DISALLOWED_RE.search(description):
            errors.append(
                f"{item}: action_description contains downstream H3 packaging"
            )
        if has_numbered_entity_label(description, identifier_context):
            errors.append(f"{item}: action_description contains numbered entity labels")
        if has_unnegated_discontinuity(description):
            errors.append(
                f"{item}: discontinuity language is forbidden; jump cuts, authored cuts, "
                "teleportation, and camera resets are invalid"
            )
        environment_path = (
            [previous_environment_id] if previous_environment_id is not None else []
        ) + current_environment_ids
        environment_changed = any(
            left != right for left, right in zip(environment_path, environment_path[1:])
        )
        if environment_changed:
            plan_and_description = f"{current.get('action_plan', '')} {description}"
            translated = isinstance(control, list) and has_translation(control)
            if (
                current.get("action_type") != "navigation"
                or not translated
                or not PHYSICAL_BRIDGE_RE.search(plan_and_description)
            ):
                errors.append(
                    f"{item}: unexplained spatial discontinuity between environments; "
                    "a navigation action must show a visible physical route and translation"
                )
        if current_environment_ids:
            previous_environment_id = current_environment_ids[-1]
        ego_token = (
            ("我" in description)
            if language == "Chinese"
            else bool(re.search(r"\b(?:I|my)\b", description, re.IGNORECASE))
        )
        if not ego_token:
            errors.append(f"{item}: action_description must narratively reference Ego")
        for ref in refs:
            for utterance in extract_utterances(ref):
                if utterance not in description:
                    errors.append(
                        f"{item}: referenced utterance is absent from action_description"
                    )
        if refs and not extract_utterances(description):
            errors.append(f"{item}: dialogue action_description lacks quoted speech")
        if not refs and extract_utterances(description):
            warnings.append(f"{item}: quoted text exists without dialogue_refs")
        if not nonempty(current.get("overall_soundscape")):
            errors.append(
                f"{item}: overall_soundscape is required for Agents-only compilation"
            )

    if valid_actions and len(valid_actions) == len(actions):
        fps = render.get("fps")
        if isinstance(fps, (int, float)) and not isinstance(fps, bool) and fps > 0:
            try:
                expected_repeats = expected_action_repeats(valid_actions, float(fps))
                for index, (schedule, expected) in enumerate(
                    zip(control_schedules, expected_repeats), start=1
                ):
                    if schedule is not None and len(schedule) != expected:
                        errors.append(
                            f"{label}: action {index}: control has {len(schedule)} steps; "
                            f"expected {expected} from timestamps and the case repeat budget"
                        )
            except Exception as exc:
                errors.append(f"{label}: cannot derive control repeat schedule: {exc}")

    return errors, warnings, valid_actions
