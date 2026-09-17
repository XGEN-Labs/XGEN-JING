"""Generate story plans and timed actions from text and reference images."""

from __future__ import annotations

import base64
import json
import mimetypes
import re
from pathlib import Path
from typing import Any

from .common import (
    PROMPTS_DIR,
    WorkflowError,
    call_vlm_json,
    ensure_targets_absent,
    file_digest,
    load_prompt,
    read_json,
    write_json_exclusive,
)
from .normalize import normalize_actions, normalize_story_decision
from .references import validate_references
from .validation import actions as action_validator
from .validation import check, complexity
from .validation import story as story_validator


def generate_story(
    client: Any,
    model: str,
    source_input: str,
    base_name: str,
    output_path: Path,
    *,
    validate: bool = True,
    reference_images: tuple[Path, ...] | list[Path] = (),
) -> Path:
    raw_response_path = output_path.with_name(f"{base_name}_story_response.txt")
    response_metadata_path = output_path.with_name(
        f"{base_name}_story_response_metadata.json"
    )
    ensure_targets_absent((raw_response_path, response_metadata_path))
    user_message = json.dumps(
        {"base_name": base_name, "input": source_input},
        ensure_ascii=False,
        indent=2,
    )
    if reference_images:
        content = [{"type": "text", "text": user_message}]
        for index, image_path in enumerate(reference_images, 1):
            image_path = Path(image_path)
            try:
                encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
            except OSError as exc:
                raise WorkflowError(
                    f"Cannot read reference image {image_path}: {exc}"
                ) from exc
            mime = mimetypes.guess_type(image_path.name)[0]
            if mime not in {"image/png", "image/jpeg", "image/webp"}:
                raise WorkflowError(f"Unsupported reference image: {image_path}")
            content.extend(
                [
                    {"type": "text", "text": f"<Picture {index}>: {image_path.name}"},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime};base64,{encoded}"},
                    },
                ]
            )
        user_message = content
    story = call_vlm_json(
        client=client,
        model=model,
        system_prompt=load_prompt(PROMPTS_DIR / "story.md"),
        user_message=user_message,
        expected_type=dict,
        max_tokens=16384,
        raw_response_path=raw_response_path,
        response_metadata_path=response_metadata_path,
    )
    if not reference_images:
        story["ref"] = []
    refs = story.get("ref")
    if (
        not isinstance(refs, list)
        or len(refs) != len(reference_images)
        or any(not isinstance(caption, str) or not caption.strip() for caption in refs)
    ):
        raise WorkflowError(
            "Story generation ref must contain one nonempty caption per reference image, in input order"
        )
    story["reference_images"] = [str(Path(p).resolve()) for p in reference_images]
    validate_references(story, story["reference_images"])
    story["base_name"] = base_name
    story, changes = normalize_story_decision(story)
    for change in changes:
        print("CHANGE Story generation", change)
    print(f"NORMALIZED Story generation changes={len(changes)}")
    write_json_exclusive(output_path, story)
    if validate:
        errors, warnings = story_validator.validate_document(story, "Story")
        check(errors, warnings, "Story generation")
    return output_path


def _repair_missing_action_id(content: str) -> str:
    return re.sub(
        r'(?m)^([ \t]*)"action_id"[ \t]*:[ \t]*"timestamp"[ \t]*:',
        r'\1"action_id": null,\n\1"timestamp":',
        content,
    )


def generate_actions(
    client: Any,
    model: str,
    story_path: Path,
    environment_path: Path,
    agents_path: Path,
    *,
    validate: bool = True,
) -> tuple[Path, Path]:
    story = read_json(story_path, dict)
    envelope = call_vlm_json(
        client,
        model,
        load_prompt(PROMPTS_DIR / "actions.md"),
        json.dumps(story, ensure_ascii=False, indent=2),
        expected_type=dict,
        max_tokens=16384,
        json_text_preprocessor=_repair_missing_action_id,
    )
    if set(envelope) != {"environment_intermediate", "agents_intermediate"}:
        raise WorkflowError(
            "Action generation must return environment_intermediate and agents_intermediate"
        )
    environment, agents = (
        envelope["environment_intermediate"],
        envelope["agents_intermediate"],
    )
    if not isinstance(environment, dict) or not isinstance(agents, dict):
        raise WorkflowError("Action generation outputs must be JSON objects")
    if story.get("_pipeline") != {"schema_version": "6.7", "stage": 1}:
        raise WorkflowError("Story pipeline metadata must match schema 6.7")
    environment["_pipeline"] = {
        "schema_version": "6.7",
        "stage": 2,
        "story_decision_sha256": file_digest(story_path),
    }
    # Environment IDs are needed for normalization even when optional checks are off.
    ids, errors = action_validator.validate_environment(environment, "Environment")
    check(errors, [], "Action generation")
    agents["reference_images"] = story.get("reference_images", [])
    validate_references(environment, agents["reference_images"])
    validate_references(agents, agents["reference_images"])
    agents, changes = normalize_actions(agents, ids)
    for change in changes:
        print(f"CHANGE Action generation: {change}")
    write_json_exclusive(environment_path, environment)
    agents["_pipeline"] = {
        **environment["_pipeline"],
        "environment_sha256": file_digest(environment_path),
    }
    if validate:
        errors, warnings, _ = action_validator.validate_document(agents, "Agents", ids)
        check(errors, warnings, "Action generation")
        errors, warnings = complexity.validate_document(agents)
        check(errors, warnings, "Action generation complexity")
    write_json_exclusive(agents_path, agents)
    return environment_path, agents_path
