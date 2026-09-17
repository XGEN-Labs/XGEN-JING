"""Translate case narration while preserving dialogue, timing and controls."""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any

from .common import (
    PROMPTS_DIR,
    WorkflowError,
    call_vlm_json,
    load_prompt,
    read_json,
    write_json_exclusive,
)
from .references import validate_pair
from .validation import cases as case_validator
from .validation import check
from .validation.english import compare_pair

CHINESE_OPENING = "第一人称POV。"
ENGLISH_OPENING = "First-person POV."
DIALOGUE_WRAPPER_RE = re.compile(
    r"<d>\s*\[(?:Chinese|English)\]\s*.*?\s*</d>",
    re.IGNORECASE | re.DOTALL,
)


def _source_language(document: list[Any]) -> str:
    languages: set[str] = set()
    for case in document:
        if not isinstance(case, dict) or not isinstance(case.get("chunks"), list):
            raise WorkflowError("H3 cases must contain a chunks array")
        for chunk in case["chunks"]:
            prompt = chunk.get("prompt") if isinstance(chunk, dict) else None
            if not isinstance(prompt, str):
                raise WorkflowError("Every H3 chunk must contain a prompt string")
            if prompt.startswith(CHINESE_OPENING):
                languages.add("Chinese")
            elif prompt.startswith(ENGLISH_OPENING):
                languages.add("English")
            else:
                raise WorkflowError("H3 prompt language cannot be identified")
    if len(languages) != 1:
        raise WorkflowError("H3 source must use one consistent prompt language")
    return languages.pop()


def _copy_english_document(document: list[Any]) -> list[Any]:
    copied = copy.deepcopy(document)
    for case in copied:
        save_name = case.get("save_name") if isinstance(case, dict) else None
        if not isinstance(save_name, str) or not save_name.lower().endswith(".mp4"):
            raise WorkflowError("English H3 source save_name must end in .mp4")
        stem = save_name[:-4]
        if stem.lower().endswith("_en"):
            raise WorkflowError(
                "English H3 source save_name must not already end in _en"
            )
        case["save_name"] = f"{stem}_en.mp4"
    return copied


def _restore_source_dialogue_blocks(
    source_document: list[Any], localized_document: list[Any]
) -> list[Any]:
    """Restore complete dialogue wrappers without changing document structure."""
    restored = copy.deepcopy(localized_document)
    if len(source_document) != len(restored):
        return restored
    for source_case, localized_case in zip(source_document, restored):
        if not isinstance(source_case, dict) or not isinstance(localized_case, dict):
            continue
        source_chunks = source_case.get("chunks")
        localized_chunks = localized_case.get("chunks")
        if not isinstance(source_chunks, list) or not isinstance(
            localized_chunks, list
        ):
            continue
        if len(source_chunks) != len(localized_chunks):
            continue
        for source_chunk, localized_chunk in zip(source_chunks, localized_chunks):
            if not isinstance(source_chunk, dict) or not isinstance(
                localized_chunk, dict
            ):
                continue
            source_prompt = source_chunk.get("prompt")
            localized_prompt = localized_chunk.get("prompt")
            if not isinstance(source_prompt, str) or not isinstance(
                localized_prompt, str
            ):
                continue
            source_dialogues = [
                match.group(0) for match in DIALOGUE_WRAPPER_RE.finditer(source_prompt)
            ]
            localized_matches = list(DIALOGUE_WRAPPER_RE.finditer(localized_prompt))
            if len(source_dialogues) != len(localized_matches):
                continue
            replacements = iter(source_dialogues)
            localized_chunk["prompt"] = DIALOGUE_WRAPPER_RE.sub(
                lambda _match: next(replacements), localized_prompt
            )
    return restored


def localize_cases(
    client: Any,
    model: str,
    h3_path: Path,
    english_path: Path,
    *,
    validate: bool = True,
) -> Path:
    h3_document = read_json(h3_path, list)
    if _source_language(h3_document) == "English":
        english_document = _copy_english_document(h3_document)
    else:
        english_document = call_vlm_json(
            client=client,
            model=model,
            system_prompt=load_prompt(PROMPTS_DIR / "english.md"),
            user_message=json.dumps(h3_document, ensure_ascii=False, indent=2),
            expected_type=list,
            max_tokens=16384,
        )
        english_document = _restore_source_dialogue_blocks(
            h3_document, english_document
        )
    validate_pair(h3_document, english_document)
    if validate:
        errors, warnings = [], []
        case_validator.validate_document(
            english_document, "English cases", errors, warnings
        )
        compare_pair(h3_document, english_document, errors)
        check(errors, warnings, "English localization")
    write_json_exclusive(english_path, english_document)
    return english_path
