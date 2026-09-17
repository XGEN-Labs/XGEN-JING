"""Validate Chinese-to-English localization or an English identity copy."""

from __future__ import annotations

import re
from typing import Any

from . import cases as h3_validator

CJK_TEXT_RE = re.compile(
    r"[\u3000-\u303f\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff00-\uffef"
    r"\U00020000-\U0002fa1f]"
)


def expected_english_save_name(source_name: str) -> str | None:
    if not source_name.lower().endswith(".mp4"):
        return None
    stem = source_name[:-4]
    if stem.lower().endswith("_en"):
        return None
    return f"{stem}_en.mp4"


def compare_chunk(
    source: Any,
    english: Any,
    label: str,
    errors: list[str],
) -> None:
    if not isinstance(source, dict) or not isinstance(english, dict):
        errors.append(f"{label}: both chunks must be objects")
        return
    if set(source) != set(english):
        errors.append(
            f"{label}: chunk keys changed; source={sorted(source)} "
            f"english={sorted(english)}"
        )

    for key, source_value in source.items():
        if key == "prompt" or key not in english:
            continue
        if english[key] != source_value:
            errors.append(f"{label}: non-prompt field {key!r} changed")

    source_prompt = source.get("prompt")
    english_prompt = english.get("prompt")
    if not isinstance(source_prompt, str) or not isinstance(english_prompt, str):
        return
    source_is_chinese = source_prompt.startswith(h3_validator.CHINESE_OPENING)
    source_is_english = source_prompt.startswith(h3_validator.ENGLISH_OPENING)
    if not source_is_chinese and not source_is_english:
        errors.append(
            f"{label}: English localization source prompt must use the Chinese or English opening"
        )
    if not english_prompt.startswith(h3_validator.ENGLISH_OPENING):
        errors.append(f"{label}: localized prompt must use the exact English opening")
    if source_is_english and english_prompt != source_prompt:
        errors.append(f"{label}: English source prompt must remain unchanged")
    source_dialogue = list(h3_validator.DIALOGUE_WRAPPER_RE.finditer(source_prompt))
    english_dialogue = list(h3_validator.DIALOGUE_WRAPPER_RE.finditer(english_prompt))
    if len(source_dialogue) != len(english_dialogue):
        errors.append(
            f"{label}: dialogue block count changed from "
            f"{len(source_dialogue)} to {len(english_dialogue)}"
        )
    for dialogue_index, (source_match, english_match) in enumerate(
        zip(source_dialogue, english_dialogue)
    ):
        if source_match.group(0) != english_match.group(0):
            errors.append(
                f"{label}: dialogue block {dialogue_index} must remain byte-for-byte "
                "unchanged"
            )

    # Chinese is allowed only inside dialogue blocks copied verbatim from the source.
    english_outside_dialogue = h3_validator.DIALOGUE_WRAPPER_RE.sub("", english_prompt)
    cjk_match = CJK_TEXT_RE.search(english_outside_dialogue)
    if cjk_match:
        errors.append(
            f"{label}: localized prose outside dialogue contains CJK text "
            f"{cjk_match.group(0)!r} at character {cjk_match.start()}"
        )

    source_s = set(h3_validator.S_MARKER_RE.findall(source_prompt))
    english_s = set(h3_validator.S_MARKER_RE.findall(english_prompt))
    if source_s != english_s:
        errors.append(
            f"{label}: S-marker identities changed from "
            f"{sorted(source_s)} to {sorted(english_s)}"
        )


def compare_pair(
    source: Any,
    english: Any,
    errors: list[str],
) -> tuple[int, int]:
    if not isinstance(source, list) or not isinstance(english, list):
        return 0, 0
    if len(source) != len(english):
        errors.append(f"case count changed from {len(source)} to {len(english)}")

    compared_cases = min(len(source), len(english))
    compared_chunks = 0
    for case_index in range(compared_cases):
        source_case = source[case_index]
        english_case = english[case_index]
        label = f"case {case_index}"
        if not isinstance(source_case, dict) or not isinstance(english_case, dict):
            errors.append(f"{label}: both cases must be objects")
            continue
        if set(source_case) != set(english_case):
            errors.append(
                f"{label}: case keys changed; source={sorted(source_case)} "
                f"english={sorted(english_case)}"
            )

        for key, source_value in source_case.items():
            if key in {"save_name", "chunks"} or key not in english_case:
                continue
            if english_case[key] != source_value:
                errors.append(f"{label}: case field {key!r} changed")

        source_name = source_case.get("save_name")
        english_name = english_case.get("save_name")
        if isinstance(source_name, str):
            expected_name = expected_english_save_name(source_name)
            if expected_name is None:
                errors.append(
                    f"{label}: source save_name must be an unsuffixed .mp4 basename"
                )
            elif english_name != expected_name:
                errors.append(
                    f"{label}: English save_name must be {expected_name!r}, "
                    f"got {english_name!r}"
                )

        source_chunks = source_case.get("chunks")
        english_chunks = english_case.get("chunks")
        if not isinstance(source_chunks, list) or not isinstance(english_chunks, list):
            continue
        if len(source_chunks) != len(english_chunks):
            errors.append(
                f"{label}: chunk count changed from "
                f"{len(source_chunks)} to {len(english_chunks)}"
            )
        for chunk_index, (source_chunk, english_chunk) in enumerate(
            zip(source_chunks, english_chunks)
        ):
            compared_chunks += 1
            compare_chunk(
                source_chunk,
                english_chunk,
                f"{label} chunk {chunk_index}",
                errors,
            )
    return compared_cases, compared_chunks
