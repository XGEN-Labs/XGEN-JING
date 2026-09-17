"""Ordered reference-image metadata and literal Picture identifier checks."""

import json
import re
from collections import Counter

from .common import WorkflowError

PICTURE = re.compile(r"<Picture ([1-9][0-9]*)>")
CANDIDATE = re.compile(r"<picture\b[^>]*>", re.IGNORECASE)


def validate_references(value, images):
    if not isinstance(images, list) or any(
        not isinstance(p, str) or not p for p in images
    ):
        raise WorkflowError("reference_images must be an ordered array of paths")
    text = json.dumps(value, ensure_ascii=False)
    for marker in CANDIDATE.findall(text):
        match = PICTURE.fullmatch(marker)
        if match is None or int(match.group(1)) > len(images):
            raise WorkflowError(f"Invalid or unavailable picture reference: {marker}")


def validate_pair(source, translated):
    if not isinstance(translated, list) or len(source) != len(translated):
        raise WorkflowError("Reference localization changed case count")
    for before, after in zip(source, translated):
        if not isinstance(before, dict) or not isinstance(after, dict):
            raise WorkflowError("Each localized case must be an object")
        images = before.get("reference_images", [])
        if after.get("reference_images", []) != images:
            raise WorkflowError("Localization changed reference_images or their order")
        validate_references(before, images)
        validate_references(after, images)
        left, right = before.get("chunks"), after.get("chunks")
        if not isinstance(left, list) or not isinstance(right, list):
            raise WorkflowError("Each localized case must contain a chunks list")
        if len(left) != len(right):
            raise WorkflowError("Reference localization changed chunk count")
        for index, (a, b) in enumerate(zip(left, right), 1):
            if any(
                not isinstance(chunk, dict) or not isinstance(chunk.get("prompt"), str)
                for chunk in (a, b)
            ):
                raise WorkflowError("Each localized chunk must contain a prompt string")
            if Counter(PICTURE.findall(a["prompt"])) != Counter(
                PICTURE.findall(b["prompt"])
            ):
                raise WorkflowError(
                    f"Localization changed picture references in chunk {index}"
                )
