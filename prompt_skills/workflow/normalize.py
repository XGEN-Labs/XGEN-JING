"""Conservative normalization of story plans and action schedules."""

from __future__ import annotations

import copy
import re
from collections import Counter
from typing import Any

from .validation.actions import expected_action_repeats
from .validation.controls import action_controls


def normalize_story_decision(story: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    data = copy.deepcopy(story)
    changes: list[str] = []

    def records(key):
        value = data.get(key)
        return (
            [x for x in value if isinstance(x, dict)] if isinstance(value, list) else []
        )

    def update(record, field, value, label):
        old = record.get(field)
        if old != value or type(old) is not type(value):
            record[field] = value
            changes.append(f"{label}.{field}: {old!r} -> {value!r}")

    roles = records("roles")
    ids = {r["role_id"] for r in roles if isinstance(r.get("role_id"), str)}
    aliases: dict[str, set[str]] = {}
    for role in roles:
        role_id = role.get("role_id")
        if not isinstance(role_id, str):
            continue
        for value in (role_id, role.get("prompt_reference")):
            if isinstance(value, str) and value.strip():
                aliases.setdefault(value.strip(), set()).add(role_id)

    def role_ref(value):
        if not isinstance(value, str) or value in ids:
            return value
        matches = aliases.get(value.strip(), set())
        return next(iter(matches)) if len(matches) == 1 else value

    for index, role in enumerate(roles):
        for field in ("known_information", "possessions"):
            value = role.get(field)
            if isinstance(value, str) and value.strip():
                update(role, field, [value], f"roles[{index}]")

    for index, obj in enumerate(records("objects")):
        value = obj.get("initial_owner")
        resolved = role_ref(value)
        if (
            resolved == value
            and isinstance(value, str)
            and value.strip().lower() == "none"
            and value not in ids
        ):
            resolved = "none"
        update(obj, "initial_owner", resolved, f"objects[{index}]")

    contract = data.get("story_contract")
    if isinstance(contract, dict):
        update(
            contract,
            "pov_role_id",
            role_ref(contract.get("pov_role_id")),
            "story_contract",
        )
    for key, field in (
        ("information_evidence", "role_id"),
        ("dialogue", "speaker_role_id"),
    ):
        for index, record in enumerate(records(key)):
            update(record, field, role_ref(record.get(field)), f"{key}[{index}]")

    for index, beat in enumerate(records("beats")):
        label = f"beats[{index}]"
        value = beat.get("action_type")
        if isinstance(value, str) and value.strip().lower() in (
            "navigation",
            "manipulation",
        ):
            update(beat, "action_type", value.strip().lower(), label)
        participants = beat.get("participants")
        if isinstance(participants, list):
            update(beat, "participants", [role_ref(v) for v in participants], label)

    beat_count = len(data["beats"]) if isinstance(data.get("beats"), list) else 0
    for index, record in enumerate(records("information_evidence")):
        value = record.get("learned_at_beat")
        if isinstance(value, float) and value.is_integer() and 1 <= value <= beat_count:
            update(
                record, "learned_at_beat", int(value), f"information_evidence[{index}]"
            )
        if (
            isinstance(value, str)
            and value.strip().isascii()
            and value.strip().isdigit()
        ):
            # Avoid parsing arbitrarily large integers from malformed model output.
            digits = value.strip().lstrip("0")
            if (
                digits
                and len(digits) <= len(str(beat_count))
                and 1 <= int(digits) <= beat_count
            ):
                update(
                    record,
                    "learned_at_beat",
                    int(digits),
                    f"information_evidence[{index}]",
                )
    evidence = data.get("information_evidence")
    if isinstance(evidence, list):
        expanded = []
        ordered_ids = list(
            dict.fromkeys(
                r["role_id"] for r in roles if isinstance(r.get("role_id"), str)
            )
        )
        for record in evidence:
            value = record.get("role_id") if isinstance(record, dict) else None
            targets = []
            if isinstance(value, str) and value not in ids:
                if value == "all_roles" or (value == "both" and len(ordered_ids) == 2):
                    targets = ordered_ids
                elif "," in value:
                    candidates = [role_ref(part.strip()) for part in value.split(",")]
                    if all(part in ids for part in candidates) and len(
                        set(candidates)
                    ) == len(candidates):
                        targets = candidates
            if targets:
                for target in targets:
                    item = copy.deepcopy(record)
                    item["role_id"] = target
                    expanded.append(item)
                changes.append(
                    f"information_evidence: expanded {value!r} to {targets!r}"
                )
            else:
                expanded.append(record)
        data["information_evidence"] = expanded

    # Encode non-ASCII characters without guessing a translation. Skip collisions.
    objects = records("objects")
    old_ids = [
        o.get("object_id") for o in objects if isinstance(o.get("object_id"), str)
    ]
    proposed = {}
    for old in old_ids:
        if not old or re.fullmatch(r"[a-z][a-z0-9_]*", old):
            continue
        new = "".join(
            c.lower()
            if c.isascii() and c.isalnum()
            else "_"
            if c.isascii()
            else f"_u{ord(c):x}_"
            for c in old
        )
        if not new or not ("a" <= new[0] <= "z"):
            new = "object_" + new
        proposed[old] = new
    counts = Counter(proposed.values())
    protected_ids = ids | {
        e.get("environment_id")
        for e in records("environment_requirements")
        if isinstance(e.get("environment_id"), str)
    }
    mapping = {
        old: new
        for old, new in proposed.items()
        if old_ids.count(old) == 1
        and new not in old_ids
        and counts[new] == 1
        and old not in protected_ids
        and new not in protected_ids
    }
    if mapping:
        pattern = re.compile(
            r"(?<!\w)(?:"
            + "|".join(re.escape(k) for k in sorted(mapping, key=len, reverse=True))
            + r")(?!\w)"
        )

        def replace_refs(value):
            if isinstance(value, str):
                return pattern.sub(lambda match: mapping[match.group()], value)
            if isinstance(value, list):
                return [replace_refs(v) for v in value]
            if isinstance(value, dict):
                return {k: replace_refs(v) for k, v in value.items()}
            return value

        data = replace_refs(data)
        for old, new in mapping.items():
            changes.append(f"object_id and references: {old!r} -> {new!r}")
    return data, changes


ENGLISH_VOICE_RE = re.compile(
    r"\b(?:says|speaks|responds|asks|answers|replies)\s+in "
    r"(?:her |his |their )?((?:a |an )?.{1,80}?voice)[,:]\s*['\"]",
    re.IGNORECASE,
)
CHINESE_VOICE_RE = re.compile(
    r"以([^：“”\"']{1,40}(?:声线|声音|嗓音))(?:说|问|回答|喊|回应)?[，,:：]?\s*[“\"]"
)
CHINESE_QUOTE_RE = re.compile(r"“([^”]+)”")
DOUBLE_QUOTE_RE = re.compile(r'"([^"]+)"')
SINGLE_QUOTE_RE = re.compile(r"(?<!\w)'([^'\n]+)'(?!\w)")


def _utterances(value: str) -> list[str]:
    return [
        item.strip()
        for item in (
            CHINESE_QUOTE_RE.findall(value)
            + DOUBLE_QUOTE_RE.findall(value)
            + SINGLE_QUOTE_RE.findall(value)
        )
        if item.strip()
    ]


def _extract_voice(text: str, language: str) -> str | None:
    match = (
        ENGLISH_VOICE_RE.search(text)
        if language == "English"
        else CHINESE_VOICE_RE.search(text)
    )
    if match is None:
        return None
    voice = match.group(1).strip()
    if language == "English":
        voice = re.sub(r"^(?:a|an)\s+", "", voice, flags=re.IGNORECASE)
    return voice


def _normalize_voices(
    data: dict[str, Any], actions: list[dict[str, Any]], changes: list[str]
) -> None:
    language = data["render_config"]["prompt_language"]
    npcs = data["agents"]["npcs"]
    for npc in npcs:
        if isinstance(npc.get("voice"), str) and npc["voice"].strip():
            continue
        agent_id = npc.get("agent_id")
        spoken_actions = [
            action
            for action in actions
            if action.get("speaker_agent_id") == agent_id
            and action.get("dialogue_refs")
        ]
        if not spoken_actions:
            npc["voice"] = (
                "non-speaking NPC"
                if language == "English"
                else "非说话角色，无对白声线"
            )
            changes.append(f"npc {agent_id}: added non-speaking voice marker")
            continue

        voices = {
            voice
            for action in spoken_actions
            for text in (
                action.get("action_description", ""),
                action.get("overall_soundscape", ""),
            )
            if (voice := _extract_voice(text, language))
        }
        if len(voices) != 1:
            raise ValueError(
                f"npc {agent_id}: speaking voice cannot be derived uniquely"
            )
        npc["voice"] = voices.pop()
        changes.append(f"npc {agent_id}: derived speaking voice")


def _matching_root_line(ref: str, root_lines: list[str]) -> int:
    exact = [index for index, line in enumerate(root_lines) if line == ref]
    if len(exact) == 1:
        return exact[0]

    contained = [index for index, line in enumerate(root_lines) if ref in line]
    if len(contained) == 1:
        return contained[0]

    ref_utterances = set(_utterances(ref))
    if ref_utterances:
        utterance_matches = [
            index
            for index, line in enumerate(root_lines)
            if ref_utterances.intersection(_utterances(line))
        ]
        if len(utterance_matches) == 1:
            return utterance_matches[0]
    raise ValueError(f"dialogue ref {ref!r} cannot be mapped uniquely to root dialogue")


def _normalize_dialogue(
    data: dict[str, Any], actions: list[dict[str, Any]], changes: list[str]
) -> None:
    root_lines = data["action"]["supporting_dialogue"]
    for action in actions:
        refs = action.get("dialogue_refs")
        if (
            refs == []
            and action.get("speaker_agent_id") is not None
            and not _utterances(action.get("action_description", ""))
        ):
            action["speaker_agent_id"] = None
            changes.append(
                f"action {action.get('action_id')}: cleared speaker_agent_id without dialogue"
            )
        if not refs:
            continue
        if not isinstance(refs, list) or len(refs) != 1 or not isinstance(refs[0], str):
            raise ValueError(
                "dialogue_refs must contain exactly one string when present"
            )
        index = _matching_root_line(refs[0], root_lines)
        root_line = root_lines[index]
        utterances = _utterances(root_line)
        description = action.get("action_description", "")
        for utterance in utterances:
            single_quoted = f"'{utterance}'"
            double_quoted = f'"{utterance}"'
            if single_quoted in root_line:
                root_line = root_line.replace(single_quoted, double_quoted)
                changes.append(
                    f"action {action.get('action_id')}: normalized root dialogue quotes"
                )
            if single_quoted in description:
                description = description.replace(single_quoted, double_quoted)
                changes.append(
                    f"action {action.get('action_id')}: normalized prompt dialogue quotes"
                )
        # Never invent speech for nonverbal refs or replace conflicting dialogue.
        if len(utterances) == 1 and not _utterances(description):
            utterance = utterances[0]
            if utterance in description:
                if description.count(utterance) == 1:
                    description = description.replace(utterance, f'"{utterance}"', 1)
                    changes.append(
                        f"action {action.get('action_id')}: quoted referenced utterance"
                    )
            elif action.get("speaker_agent_id"):
                description = description.rstrip() + " " + root_line
                changes.append(
                    f"action {action.get('action_id')}: restored referenced dialogue"
                )
        root_lines[index] = root_line
        action["action_description"] = description
        if refs[0] != root_line:
            action["dialogue_refs"] = [root_line]
            changes.append(
                f"action {action.get('action_id')}: expanded dialogue ref to root line"
            )


def _normalize_action_ids(
    data: dict[str, Any], actions: list[dict[str, Any]], changes: list[str]
) -> None:
    action_list = data["agents"]["ego"]["action_list"]
    for expected_id, action in enumerate(actions, start=1):
        current_id = action.get("action_id")
        if type(current_id) is not int or current_id != expected_id:
            action["action_id"] = expected_id
            changes.append(
                f"action at position {expected_id}: normalized action_id "
                f"from {current_id!r} to {expected_id}"
            )
    current_total = action_list.get("total_num")
    if type(current_total) is not int or current_total != len(actions):
        action_list["total_num"] = len(actions)
        changes.append(
            f"action_list: synchronized total_num from {current_total!r} "
            f"to {len(actions)}"
        )


def _normalize_bindings(
    data: dict[str, Any], actions: list[dict[str, Any]], changes: list[str]
) -> None:
    language = data["render_config"]["prompt_language"]
    references = [npc["prompt_reference"] for npc in data["agents"]["npcs"]]
    for action in actions:
        action_id = action.get("action_id")
        description = action["action_description"]
        for reference in references:
            normalized = re.sub(
                re.escape(reference),
                lambda _: reference,
                description,
                flags=re.IGNORECASE,
            )
            if normalized != description:
                description = normalized
                changes.append(f"action {action_id}: normalized NPC prompt reference")

        if language == "English":
            if not re.search(r"\b(?:I|my)\b", description, re.IGNORECASE):
                description = description.replace(
                    "First-person POV.",
                    "First-person POV. I remain the sole camera wearer.",
                    1,
                )
                changes.append(f"action {action_id}: added explicit Ego binding")
        elif "我" not in description:
            description = description.replace(
                "第一人称POV",
                "第一人称POV我保持唯一持镜者身份。",
                1,
            )
            changes.append(f"action {action_id}: added explicit Ego binding")
        action["action_description"] = description


def _normalize_controls(
    data: dict[str, Any], actions: list[dict[str, Any]], changes: list[str]
) -> None:
    fps = float(data["render_config"]["fps"])
    expected = expected_action_repeats(actions, fps)
    for action, repeat_count in zip(actions, expected):
        schedule = action_controls(action)
        if len(set(map(str, schedule))) != 1:
            raise ValueError(
                f"action {action.get('action_id')}: mixed control cannot be normalized"
            )
        if len(schedule) != repeat_count:
            action["control"] = [schedule[0]] * repeat_count
            changes.append(
                f"action {action.get('action_id')}: resized control to {repeat_count} repeats"
            )


def _normalize_environment_bindings(data, actions, environment_ids, changes):
    if not environment_ids:
        return
    intent = data.get("intent", {})
    if not isinstance(intent, dict):
        return
    dynamics = []
    complete = True
    for action in actions:
        entries = action.get("scene_dynamics")
        if not isinstance(entries, list) or not entries:
            complete = False
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                complete = False
                continue
            identifier = entry.get("environment_id")
            if not isinstance(identifier, str) or identifier not in environment_ids:
                complete = False
                continue
            dynamics.append(identifier)
            description = entry.get("description")
            if (
                isinstance(description, str)
                and description.strip()
                and identifier not in description
            ):
                if not any(
                    other in description
                    for other in environment_ids
                    if other != identifier
                ):
                    entry["description"] = f"{identifier}: {description}"
                    changes.append(
                        f"scene_dynamics: added environment prefix {identifier}"
                    )
    start, end = intent.get("start_environment_id"), intent.get("end_environment_id")
    if (
        complete
        and dynamics
        and isinstance(start, str)
        and isinstance(end, str)
        and start in environment_ids
        and end in environment_ids
        and dynamics[0] == start
        and dynamics[-1] == end
        and isinstance(intent.get("scene_change"), bool)
    ):
        expected = start != end
        if intent["scene_change"] != expected:
            intent["scene_change"] = expected
            changes.append(
                f"intent.scene_change: derived {expected} from environment IDs"
            )


def normalize_actions(
    data: Any, environment_ids: set[str] | None = None
) -> tuple[dict[str, Any], list[str]]:
    if not isinstance(data, dict):
        raise ValueError("Agents top level must be an object")
    normalized = copy.deepcopy(data)
    try:
        actions = normalized["agents"]["ego"]["action_list"]["actions"]
        if not isinstance(actions, list) or not actions:
            raise TypeError
        if not isinstance(normalized["action"]["supporting_dialogue"], list):
            raise TypeError
        if normalized["render_config"]["prompt_language"] not in (
            "Chinese",
            "English",
        ):
            raise TypeError
    except (KeyError, TypeError) as exc:
        raise ValueError(
            "Agents document lacks required normalization structure"
        ) from exc

    changes: list[str] = []
    _normalize_action_ids(normalized, actions, changes)
    _normalize_voices(normalized, actions, changes)
    _normalize_dialogue(normalized, actions, changes)
    _normalize_bindings(normalized, actions, changes)
    _normalize_environment_bindings(normalized, actions, environment_ids, changes)
    _normalize_controls(normalized, actions, changes)
    return normalized, changes
