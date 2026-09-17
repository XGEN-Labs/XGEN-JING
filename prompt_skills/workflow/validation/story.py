"""Validate generated story plans."""

from __future__ import annotations

import json
import re
from typing import Any

ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")
FORBIDDEN_RE = re.compile(
    r"integrated_multimodal_description|<\s*/?d\b|[（(]S\d+[）)]|\"chunks\"",
    re.IGNORECASE,
)


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_document(data: Any, label: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(data, dict):
        return [f"{label}: top level must be an object"], warnings

    pipeline = data.get("_pipeline")
    if not isinstance(pipeline, dict):
        errors.append(f"{label}: _pipeline must be an object")
    else:
        if pipeline.get("schema_version") != "6.7":
            errors.append(f"{label}: _pipeline.schema_version must be '6.7'")
        if pipeline.get("stage") != 1:
            errors.append(f"{label}: _pipeline.stage must be 1")

    if not nonempty(data.get("base_name")):
        errors.append(f"{label}: base_name must be a nonempty string")

    source = data.get("source_assessment")
    if not isinstance(source, dict):
        errors.append(f"{label}: source_assessment must be an object")
    else:
        if not nonempty(source.get("intended_event")):
            errors.append(f"{label}: source_assessment.intended_event is required")
        for field in ("hard_facts", "repairs", "discarded_details"):
            value = source.get(field)
            if not isinstance(value, list) or any(not nonempty(x) for x in value):
                errors.append(
                    f"{label}: source_assessment.{field} must be an array of strings"
                )

    contract = data.get("story_contract")
    required_contract = (
        "pov_role_id",
        "immediate_goal",
        "visible_trigger",
        "interaction_reason",
        "decisive_response",
        "visible_result",
        "next_state",
    )
    if not isinstance(contract, dict):
        errors.append(f"{label}: story_contract must be an object")
        contract = {}
    for field in required_contract:
        if not nonempty(contract.get(field)):
            errors.append(f"{label}: story_contract.{field} is required")

    roles = data.get("roles")
    role_ids: set[str] = set()
    camera_roles: list[str] = []
    prompt_references: set[str] = set()
    if not isinstance(roles, list) or not roles:
        errors.append(f"{label}: roles must be a nonempty array")
        roles = []
    for index, role in enumerate(roles):
        item = f"{label}: role {index}"
        if not isinstance(role, dict):
            errors.append(f"{item}: must be an object")
            continue
        role_id = role.get("role_id")
        if not nonempty(role_id) or not ID_RE.fullmatch(role_id):
            errors.append(f"{item}: role_id must match {ID_RE.pattern}")
        elif role_id in role_ids:
            errors.append(f"{item}: duplicate role_id {role_id!r}")
        else:
            role_ids.add(role_id)
        if role.get("is_camera_wearer") is True and nonempty(role_id):
            camera_roles.append(role_id)
        elif not isinstance(role.get("is_camera_wearer"), bool):
            errors.append(f"{item}: is_camera_wearer must be boolean")
        for field in (
            "identity",
            "prompt_reference",
            "goal",
            "capability_and_authority",
            "relationship",
            "likely_next_action",
        ):
            if not nonempty(role.get(field)):
                errors.append(f"{item}: {field} is required")
        reference = role.get("prompt_reference")
        if nonempty(reference):
            if reference in prompt_references:
                errors.append(f"{item}: prompt_reference must be unique")
            prompt_references.add(reference)
        for field in ("known_information", "possessions"):
            value = role.get(field)
            if not isinstance(value, list) or any(not nonempty(x) for x in value):
                errors.append(f"{item}: {field} must be an array of strings")
    if len(camera_roles) != 1:
        errors.append(f"{label}: exactly one role must be the camera wearer")
    if contract.get("pov_role_id") not in camera_roles:
        errors.append(
            f"{label}: story_contract.pov_role_id must name the camera wearer"
        )

    environment_requirements = data.get("environment_requirements")
    environment_ids: set[str] = set()
    if not isinstance(environment_requirements, list) or not environment_requirements:
        errors.append(f"{label}: environment_requirements must be a nonempty array")
        environment_requirements = []
    for index, environment in enumerate(environment_requirements):
        item = f"{label}: environment requirement {index}"
        if not isinstance(environment, dict):
            errors.append(f"{item}: must be an object")
            continue
        environment_id = environment.get("environment_id")
        if not nonempty(environment_id) or not ID_RE.fullmatch(environment_id):
            errors.append(f"{item}: environment_id must be a plain identifier")
        elif environment_id in environment_ids:
            errors.append(f"{item}: duplicate environment_id {environment_id!r}")
        else:
            environment_ids.add(environment_id)
        if not nonempty(environment.get("content")):
            errors.append(f"{item}: content is required")

    objects = data.get("objects")
    object_ids: set[str] = set()
    if not isinstance(objects, list):
        errors.append(f"{label}: objects must be an array")
        objects = []
    for index, obj in enumerate(objects):
        item = f"{label}: object {index}"
        if not isinstance(obj, dict):
            errors.append(f"{item}: must be an object")
            continue
        object_id = obj.get("object_id")
        if not nonempty(object_id) or not ID_RE.fullmatch(object_id):
            errors.append(f"{item}: object_id must be a plain identifier")
        elif object_id in object_ids:
            errors.append(f"{item}: duplicate object_id")
        else:
            object_ids.add(object_id)
        if not isinstance(obj.get("support_chain"), list) or not obj["support_chain"]:
            errors.append(f"{item}: support_chain must be nonempty")
        if not nonempty(obj.get("terminal_owner_or_support")):
            errors.append(f"{item}: terminal_owner_or_support is required")

    information = data.get("information_evidence")
    if not isinstance(information, list):
        errors.append(f"{label}: information_evidence must be an array")
        information = []
    for index, evidence in enumerate(information):
        item = f"{label}: information evidence {index}"
        if not isinstance(evidence, dict):
            errors.append(f"{item}: must be an object")
            continue
        if evidence.get("role_id") not in role_ids:
            errors.append(f"{item}: role_id must name a declared role")
        for field in ("fact", "source", "resulting_action"):
            if not nonempty(evidence.get(field)):
                errors.append(f"{item}: {field} is required")
        learned = evidence.get("learned_at_beat")
        if not isinstance(learned, int) or isinstance(learned, bool) or learned <= 0:
            errors.append(f"{item}: learned_at_beat must be a positive integer")

    dialogue = data.get("dialogue")
    if not isinstance(dialogue, list):
        errors.append(f"{label}: dialogue must be an array")
        dialogue = []
    for index, line in enumerate(dialogue):
        item = f"{label}: dialogue {index}"
        if not isinstance(line, dict):
            errors.append(f"{item}: must be an object")
            continue
        if line.get("speaker_role_id") not in role_ids:
            errors.append(f"{item}: speaker_role_id must name a declared role")
        if line.get("language") not in ("Chinese", "English"):
            errors.append(f"{item}: language must be Chinese or English")
        for field in ("utterance", "purpose"):
            if not nonempty(line.get(field)):
                errors.append(f"{item}: {field} is required")

    beats = data.get("beats")
    if not isinstance(beats, list) or not beats:
        errors.append(f"{label}: beats must be a nonempty array")
        beats = []
    total_duration = 0.0
    for index, beat in enumerate(beats, start=1):
        item = f"{label}: beat {index}"
        if not isinstance(beat, dict):
            errors.append(f"{item}: must be an object")
            continue
        if beat.get("beat_id") != index:
            errors.append(f"{item}: beat_id must be sequential and equal {index}")
        duration = beat.get("duration_seconds")
        if (
            not isinstance(duration, (int, float))
            or isinstance(duration, bool)
            or duration <= 0
        ):
            errors.append(f"{item}: duration_seconds must be positive")
        else:
            total_duration += float(duration)
        if not nonempty(beat.get("action_type")):
            errors.append(f"{item}: action_type must be a nonempty string")
        for field in ("dominant_change", "plan", "end_state"):
            if not nonempty(beat.get(field)):
                errors.append(f"{item}: {field} is required")
        participants = beat.get("participants")
        if not isinstance(participants, list) or any(
            value not in role_ids for value in participants
        ):
            errors.append(f"{item}: participants must reference declared roles")
        environments = beat.get("environment_ids")
        if (
            not isinstance(environments, list)
            or not environments
            or any(value not in environment_ids for value in environments)
        ):
            errors.append(
                f"{item}: environment_ids must reference declared environments"
            )
    duration_epsilon = 1e-6
    if total_duration > 60.0 + duration_epsilon:
        errors.append(
            f"{label}: total beat duration {total_duration:.3f}s exceeds 60 seconds"
        )
    if total_duration <= 15.0 + duration_epsilon:
        advisory_beat_limit = 5
    elif total_duration <= 24.0 + duration_epsilon:
        advisory_beat_limit = 7
    elif total_duration <= 30.0 + duration_epsilon:
        advisory_beat_limit = 9
    elif total_duration <= 50.0 + duration_epsilon:
        advisory_beat_limit = 18
    else:
        advisory_beat_limit = 24
    if len(beats) > advisory_beat_limit:
        warnings.append(
            f"{label}: {len(beats)} beats may be dense for {total_duration:.1f}s"
        )
    for index, evidence in enumerate(information):
        if isinstance(evidence, dict) and isinstance(
            evidence.get("learned_at_beat"), int
        ):
            if evidence["learned_at_beat"] > len(beats):
                errors.append(
                    f"{label}: information evidence {index} references a missing beat"
                )
    spatial = data.get("spatial_plan")
    if not isinstance(spatial, dict):
        errors.append(f"{label}: spatial_plan must be an object")
    else:
        for field in ("camera_start", "terminal_composition"):
            if not nonempty(spatial.get(field)):
                errors.append(f"{label}: spatial_plan.{field} is required")
        for field in ("stable_anchors", "route"):
            if not isinstance(spatial.get(field), list) or not spatial[field]:
                errors.append(f"{label}: spatial_plan.{field} must be nonempty")

    render = data.get("render_policy")
    if not isinstance(render, dict):
        errors.append(f"{label}: render_policy must be an object")
    else:
        if not nonempty(render.get("save_name")) or not render["save_name"].endswith(
            ".mp4"
        ):
            errors.append(f"{label}: render_policy.save_name must end in .mp4")
        for field in ("seed", "height", "width", "num_inference_steps"):
            if (
                not isinstance(render.get(field), int)
                or isinstance(render.get(field), bool)
                or render[field] <= 0
            ):
                errors.append(
                    f"{label}: render_policy.{field} must be a positive integer"
                )
        fps = render.get("fps")
        if not isinstance(fps, (int, float)) or isinstance(fps, bool) or fps <= 0:
            errors.append(f"{label}: render_policy.fps must be positive")
        if render.get("prompt_language") not in ("Chinese", "English"):
            errors.append(
                f"{label}: render_policy.prompt_language must be Chinese or English"
            )
        for field in ("visual_style", "non_diegetic_music"):
            if not nonempty(render.get(field)):
                errors.append(f"{label}: render_policy.{field} is required")
        if render.get("control_signal") != "camera_delta":
            errors.append(f"{label}: render_policy.control_signal must be camera_delta")
        if render.get("discrete_camera") is not True:
            errors.append(f"{label}: render_policy.discrete_camera must be true")

    serialized = json.dumps(data, ensure_ascii=False)
    if FORBIDDEN_RE.search(serialized):
        errors.append(
            f"{label}: Story Decision contains downstream H3 syntax or S markers"
        )
    return errors, warnings
