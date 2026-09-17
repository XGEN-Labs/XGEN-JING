"""Deterministically compile H3 Official using Agents Intermediate only."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .common import read_json, write_json_exclusive
from .references import validate_references
from .validation import actions as agent_validator
from .validation import cases as case_validator
from .validation import check
from .validation.controls import action_controls

QUOTE_RE = re.compile(r"(“[^”]*”|\"[^\"]*\")")


def strip_pov(description: str, language: str) -> str:
    if language == "Chinese":
        if not description.startswith("第一人称POV"):
            raise ValueError("Chinese action_description must begin with 第一人称POV")
        return description[len("第一人称POV") :].lstrip("。．. ")
    opening = "First-person POV"
    if description.startswith(f"{opening}."):
        return description[len(opening) + 1 :].lstrip()
    if description.startswith(f"{opening} "):
        return description[len(opening) :].lstrip()
    raise ValueError("English action_description must begin with First-person POV")


def annotate_outside_quotes(
    body: str,
    language: str,
    npc_references: list[tuple[str, str]],
) -> str:
    def annotate(segment: str) -> str:
        if language == "Chinese":
            segment = segment.replace("我", "我（S1）")
            for reference, marker in sorted(
                npc_references, key=lambda item: len(item[0]), reverse=True
            ):
                segment = segment.replace(reference, f"{reference}（{marker}）")
        else:
            segment = re.sub(r"\bI\b", "I (S1)", segment)
            segment = re.sub(r"\bmy\b", "my (S1)", segment)
            segment = re.sub(r"\bMy\b", "My (S1)", segment)
            for reference, marker in sorted(
                npc_references, key=lambda item: len(item[0]), reverse=True
            ):
                segment = segment.replace(reference, f"{reference} ({marker})")
        return segment

    parts = QUOTE_RE.split(body)
    return "".join(
        part if QUOTE_RE.fullmatch(part) else annotate(part) for part in parts
    )


def wrap_dialogue(body: str, language: str) -> str:
    if language == "Chinese":
        return re.sub(r"“([^”]+)”", r"<d>[Chinese] \1</d>", body)
    return re.sub(r"\"([^\"]+)\"", r"<d>[English] \1</d>", body)


def compile_document(
    agents_data: dict[str, Any], *, validate: bool = True
) -> list[dict[str, Any]]:
    if validate:
        errors, warnings, actions = agent_validator.validate_document(
            agents_data, "agents input", None
        )
        if errors:
            raise ValueError("invalid Agents Intermediate: " + "; ".join(errors))
        if warnings:
            raise ValueError(
                "Agents Intermediate warnings must be reviewed before compile: "
                + "; ".join(warnings)
            )

    else:
        actions = agents_data["agents"]["ego"]["action_list"]["actions"]

    render = agents_data["render_config"]
    language = render["prompt_language"]
    npcs = agents_data["agents"]["npcs"]
    ego = agents_data["agents"]["ego"]
    agent_records = {ego["agent_id"]: (ego, "S1")}
    npc_references: list[tuple[str, str]] = []
    for index, npc in enumerate(npcs, start=2):
        marker = f"S{index}"
        agent_records[npc["agent_id"]] = (npc, marker)
        npc_references.append((npc["prompt_reference"], marker))

    schedules = [action_controls(action) for action in actions]
    repeat_total = sum(map(len, schedules))

    opening = (
        "第一人称POV。integrated_multimodal_description: [Shot 1] Live-action, cinematic."
        if language == "Chinese"
        else "First-person POV. integrated_multimodal_description: [Shot 1] Live-action, cinematic."
    )
    chunks: list[dict[str, Any]] = []
    for action, schedule in zip(actions, schedules):
        body = strip_pov(action["action_description"], language)
        body = annotate_outside_quotes(body, language, npc_references)
        speaker_declaration = ""
        if action["dialogue_refs"]:
            speaker, marker = agent_records[action["speaker_agent_id"]]
            reference = speaker["prompt_reference"]
            voice = speaker["voice"]
            if language == "Chinese":
                speaker_declaration = f"本段说话人：{reference}（{marker}，{voice}）。"
            else:
                speaker_declaration = (
                    f"Current speaker: {reference} ({marker}, {voice}). "
                )
            body = wrap_dialogue(body, language)
        soundscape = annotate_outside_quotes(
            action["overall_soundscape"], language, npc_references
        )
        style_separator = "。" if language == "Chinese" else ". "
        prompt = (
            f"{opening} {render['visual_style']}{style_separator}{speaker_declaration}{body}"
            f"\n\noverall_soundscape: {soundscape}"
            f"\n\nnon_diegetic_music: {render['non_diegetic_music']}"
        )
        chunks.append(
            {
                "prompt": prompt,
                "repeat": len(schedule),
                "control": list(schedule),
            }
        )

    case: dict[str, Any] = {
        "save_name": render["save_name"],
        "seed": render["seed"],
        "height": render["height"],
        "width": render["width"],
        "num_frames": 17 * repeat_total + 5,
        "chunks": chunks,
        "reference_images": list(agents_data.get("reference_images", [])),
    }
    return [case]


def compile_cases(agents_path: Path, h3_path: Path, *, validate: bool = True) -> Path:
    agents = read_json(agents_path, dict)
    cases = compile_document(agents, validate=validate)
    for case in cases:
        validate_references(case, case["reference_images"])
    if validate:
        errors, warnings = [], []
        case_validator.validate_document(cases, "Cases", errors, warnings)
        check(errors, warnings, "Compilation")
    write_json_exclusive(h3_path, cases)
    return h3_path
