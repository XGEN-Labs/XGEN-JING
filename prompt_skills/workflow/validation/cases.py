"""Validate standalone H3 Official JSON case files using only Python stdlib."""

from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any

from .controls import validate_control
from .entities import is_physical_identifier

CHINESE_OPENING = (
    "第一人称POV。integrated_multimodal_description: [Shot 1] Live-action, cinematic."
)
ENGLISH_OPENING = (
    "First-person POV. integrated_multimodal_description: "
    "[Shot 1] Live-action, cinematic."
)
SOUNDSCAPE_MARKER = "\n\noverall_soundscape:"
MUSIC_MARKER = "\n\nnon_diegetic_music:"
DIALOGUE_WRAPPER_RE = re.compile(
    r"<d>\s*\[(Chinese|English)\]\s*(.*?)\s*</d>",
    re.IGNORECASE | re.DOTALL,
)
DIALOGUE_MARKUP_TOKEN_RE = re.compile(
    r"<\s*/?\s*d\s*>|\[(?:Chinese|English)\]", re.IGNORECASE
)
DISALLOWED_ENTITY_RE = re.compile(r"(?<![A-Za-z0-9_])(?:O\d+|B\d+)(?![A-Za-z0-9_])")
S_MARKER_RE = re.compile(r"(?<![A-Za-z0-9_])S([1-9]\d*)(?![A-Za-z0-9_])")
FORBIDDEN_AUDIO_MODE_RE = re.compile(
    "\u753b\u5916\u97f3|\u65c1\u767d|voice[- ]?over|off[- ]screen narration",
    re.IGNORECASE,
)
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


def is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def nearest_repeat_budget(target_seconds: float, fps: float) -> int:
    raw = (fps * target_seconds - 5.0) / 17.0
    return max(1, math.floor(raw + 0.5))


def remove_quoted_text(value: str) -> str:
    value = DIALOGUE_WRAPPER_RE.sub("", value)
    value = re.sub(r"“[^”]*”", "", value)
    return re.sub(r'"[^"]*"', "", value)


def has_unnegated_discontinuity(value: str) -> bool:
    for match in DISCONTINUITY_RE.finditer(value):
        left_context = value[max(0, match.start() - 32) : match.start()]
        if not NEGATION_RE.search(left_context):
            return True
    return False


def validate_prompt(
    prompt: str,
    label: str,
    errors: list[str],
    warnings: list[str],
    identifier_context: str = "",
) -> None:
    if not (prompt.startswith(CHINESE_OPENING) or prompt.startswith(ENGLISH_OPENING)):
        errors.append(
            f"{label}: prompt must begin with the exact Chinese or English "
            "H3 Official first-person opening"
        )

    soundscape_at = prompt.find(SOUNDSCAPE_MARKER)
    music_at = prompt.find(MUSIC_MARKER)
    if soundscape_at < 0:
        errors.append(
            f"{label}: missing blank-line-separated overall_soundscape section"
        )
    if music_at < 0:
        errors.append(
            f"{label}: missing blank-line-separated non_diegetic_music section"
        )
    if soundscape_at >= 0 and music_at >= 0:
        if soundscape_at >= music_at:
            errors.append(f"{label}: soundscape must precede non-diegetic music")
        else:
            soundscape = prompt[
                soundscape_at + len(SOUNDSCAPE_MARKER) : music_at
            ].strip()
            music = prompt[music_at + len(MUSIC_MARKER) :].strip()
            if not soundscape:
                errors.append(f"{label}: overall_soundscape must not be empty")
            if not music:
                errors.append(f"{label}: non_diegetic_music must not be empty")

    visible_prompt = prompt.split(SOUNDSCAPE_MARKER, 1)[0]
    wrapped_turns = list(DIALOGUE_WRAPPER_RE.finditer(visible_prompt))
    markup_remainder = DIALOGUE_WRAPPER_RE.sub("", visible_prompt)
    for match in DIALOGUE_MARKUP_TOKEN_RE.finditer(markup_remainder):
        errors.append(f"{label}: malformed or stray dialogue markup {match.group(0)!r}")
    for match in DISALLOWED_ENTITY_RE.finditer(prompt):
        if is_physical_identifier(prompt, match, identifier_context):
            continue
        errors.append(f"{label}: object or beat label {match.group(0)!r} is forbidden")
    if FORBIDDEN_AUDIO_MODE_RE.search(prompt):
        errors.append(f"{label}: voice-over and off-screen narration are not supported")

    narrative_text = remove_quoted_text(prompt)
    if prompt.startswith(CHINESE_OPENING):
        if "我（S1）" not in narrative_text:
            errors.append(f"{label}: every Chinese chunk must contain 我（S1）")
        if re.search(r"我(?!（S1）)", narrative_text):
            errors.append(
                f"{label}: every narrative 我 outside quoted dialogue must be followed by （S1）"
            )
    natural_dialogue_text = DIALOGUE_WRAPPER_RE.sub("", visible_prompt)
    chinese_utterances = min(
        natural_dialogue_text.count("“"), natural_dialogue_text.count("”")
    )
    ascii_utterances = natural_dialogue_text.count('"') // 2
    utterance_count = len(wrapped_turns) + chinese_utterances + ascii_utterances
    speaker_label = (
        "本段说话人：" if prompt.startswith(CHINESE_OPENING) else "Current speaker:"
    )
    if utterance_count and visible_prompt.count(speaker_label) != 1:
        errors.append(
            f"{label}: a dialogue chunk must contain exactly one {speaker_label!r} declaration"
        )
    if utterance_count and speaker_label in visible_prompt:
        declaration_end = "。" if prompt.startswith(CHINESE_OPENING) else "."
        declaration = visible_prompt.split(speaker_label, 1)[1].split(
            declaration_end, 1
        )[0]
        if len(S_MARKER_RE.findall(declaration)) != 1:
            errors.append(
                f"{label}: speaker declaration must contain exactly one S identifier"
            )
    if utterance_count > 1:
        warnings.append(
            f"{label}: multiple quoted utterances may contain more than one speaker turn"
        )
    if has_unnegated_discontinuity(prompt):
        errors.append(
            f"{label}: discontinuity language is forbidden; jump cuts, authored cuts, "
            "teleportation, and camera resets are invalid"
        )


def validate_case(
    case: Any,
    label: str,
    fps: float,
    target_seconds: float | None,
    errors: list[str],
    warnings: list[str],
) -> tuple[Any, Any, int, float] | None:
    if not isinstance(case, dict):
        errors.append(f"{label}: case must be an object")
        return None

    save_name = case.get("save_name")
    if not isinstance(save_name, str) or not save_name.strip():
        errors.append(f"{label}: save_name must be a nonempty string")
    elif (
        Path(save_name).name != save_name
        or "/" in save_name
        or "\\" in save_name
        or not save_name.lower().endswith(".mp4")
    ):
        errors.append(
            f"{label}: save_name must be a filesystem basename ending in .mp4"
        )

    seed = case.get("seed")
    if not is_int(seed):
        errors.append(f"{label}: seed must be an integer")

    for field in ("height", "width", "num_frames"):
        value = case.get(field)
        if not is_int(value) or value <= 0:
            errors.append(f"{label}: {field} must be a positive integer")

    allowed = {
        "save_name",
        "seed",
        "height",
        "width",
        "num_frames",
        "chunks",
        "reference_images",
    }
    if set(case) - allowed:
        errors.append(
            f"{label}: unsupported case fields: {sorted(set(case) - allowed)}"
        )
    for field in ("height", "width"):
        if is_int(case.get(field)) and case[field] % 32:
            errors.append(f"{label}: {field} must be divisible by 32")
    references = case.get("reference_images", [])
    if not isinstance(references, list) or any(
        not isinstance(p, str) or not p for p in references
    ):
        errors.append(f"{label}: reference_images must be an ordered list of paths")

    chunks = case.get("chunks")
    if not isinstance(chunks, list) or not chunks:
        errors.append(f"{label}: chunks must be a nonempty array")
        return save_name, seed, 0, 0.0

    identifier_context = "\n".join(
        chunk.get("prompt", "")
        for chunk in chunks
        if isinstance(chunk, dict) and isinstance(chunk.get("prompt"), str)
    )
    repeat_total = 0
    marker_ids: set[int] = set()
    for chunk_index, chunk in enumerate(chunks):
        chunk_label = f"{label} chunk {chunk_index}"
        if not isinstance(chunk, dict):
            errors.append(f"{chunk_label}: chunk must be an object")
            continue
        if set(chunk) - {"prompt", "repeat", "control"}:
            errors.append(
                f"{chunk_label}: only prompt, repeat and control are accepted"
            )
        prompt = chunk.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            errors.append(f"{chunk_label}: prompt must be a nonempty string")
        else:
            validate_prompt(prompt, chunk_label, errors, warnings, identifier_context)
            marker_ids.update(int(value) for value in S_MARKER_RE.findall(prompt))

        repeat = chunk.get("repeat")
        if not is_int(repeat) or repeat <= 0:
            errors.append(f"{chunk_label}: repeat must be a positive integer")
        else:
            repeat_total += repeat

        controls = chunk.get("control")
        if not isinstance(controls, list) or len(controls) != repeat:
            errors.append(f"{chunk_label}: control must be a list of length repeat")
        else:
            for control in controls:
                validate_control(control, chunk_label, errors)

    if not marker_ids or 1 not in marker_ids:
        errors.append(f"{label}: S-role map must include camera wearer S1")
    elif marker_ids != set(range(1, max(marker_ids) + 1)):
        errors.append(
            f"{label}: S-role identifiers must be contiguous from S1; found {sorted(marker_ids)}"
        )

    expected_frames = 17 * repeat_total + 5
    if case.get("num_frames") != expected_frames:
        errors.append(
            f"{label}: num_frames={case.get('num_frames')!r}, expected "
            f"17 * {repeat_total} + 5 = {expected_frames}"
        )

    effective_seconds = expected_frames / fps
    if target_seconds is not None:
        desired_repeats = nearest_repeat_budget(target_seconds, fps)
        if repeat_total != desired_repeats:
            desired_frames = 17 * desired_repeats + 5
            warnings.append(
                f"{label}: repeat total {repeat_total} does not match the nearest "
                f"budget {desired_repeats} for {target_seconds:g}s at {fps:g}fps "
                f"({desired_frames / fps:.3f}s effective)"
            )

    return save_name, seed, repeat_total, effective_seconds


def validate_document(
    document: Any,
    label: str,
    errors: list[str],
    warnings: list[str],
) -> tuple[int, int]:
    if not isinstance(document, list) or not document:
        errors.append(f"{label}: top level must be a nonempty array")
        return 0, 0

    seen_names: dict[str, int] = {}
    seen_seeds: dict[int, int] = {}
    chunks = 0
    for case_index, case in enumerate(document):
        case_label = f"{label}: case {case_index}"
        result = validate_case(case, case_label, 24.0, None, errors, warnings)
        if isinstance(case, dict) and isinstance(case.get("chunks"), list):
            chunks += len(case["chunks"])
        if result is None:
            continue
        save_name, seed, _, _ = result
        if isinstance(save_name, str):
            if save_name in seen_names:
                errors.append(
                    f"{case_label}: duplicate save_name {save_name!r}; "
                    f"first used by case {seen_names[save_name]}"
                )
            else:
                seen_names[save_name] = case_index
        if is_int(seed):
            if seed in seen_seeds:
                errors.append(
                    f"{case_label}: duplicate seed {seed}; "
                    f"first used by case {seen_seeds[seed]}"
                )
            else:
                seen_seeds[seed] = case_index
    return len(document), chunks
