"""Verify saved provenance and deterministic compilation."""

from pathlib import Path

from .common import file_digest, read_json
from .compiler import compile_document
from .references import validate_pair
from .validation import check
from .validation.english import compare_pair


def audit(
    story: Path, environment: Path, agents: Path, h3: Path, english: Path
) -> None:
    story_data = read_json(story, dict)
    environment_data = read_json(environment, dict)
    agents_data = read_json(agents, dict)
    source = read_json(h3, list)
    translated = read_json(english, list)
    errors = []
    story_hash, environment_hash = file_digest(story), file_digest(environment)
    environment_pipeline = environment_data.get("_pipeline", {})
    agents_pipeline = agents_data.get("_pipeline", {})
    if environment_pipeline.get("story_decision_sha256") != story_hash:
        errors.append("environment provenance does not match story")
    if agents_pipeline.get("story_decision_sha256") != story_hash:
        errors.append("agents provenance does not match story")
    if agents_pipeline.get("environment_sha256") != environment_hash:
        errors.append("agents provenance does not match environment")
    if agents_data.get("reference_images", []) != story_data.get(
        "reference_images", []
    ):
        errors.append("Action generation changed reference image order")
    if source != compile_document(agents_data):
        errors.append("cases differ from deterministic compilation")
    validate_pair(source, translated)
    compare_pair(source, translated, errors)
    check(errors, [], "Final audit")
