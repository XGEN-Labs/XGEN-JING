"""Shared boundaries for the prompt workflow."""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = PACKAGE_ROOT / "prompts"


class WorkflowError(RuntimeError):
    """A user-actionable workflow failure."""


@dataclass(frozen=True)
class VLMConfig:
    base_url: str
    api_key: str = field(repr=False)
    model: str


def load_config(
    base_url: str | None = None,
    model: str | None = None,
    environ: Mapping[str, str] | None = None,
) -> VLMConfig:
    values = os.environ if environ is None else environ
    api_key = values.get("VLM_API_KEY", "").strip()
    if not api_key:
        raise WorkflowError("VLM_API_KEY is required")
    resolved_base_url = (
        base_url if base_url is not None else values.get("VLM_BASE_URL", "")
    ).strip()
    resolved_model = (
        model if model is not None else values.get("VLM_MODEL", "")
    ).strip()
    if not resolved_base_url:
        raise WorkflowError("VLM_BASE_URL or --base-url is required")
    if not resolved_model:
        raise WorkflowError("VLM_MODEL or --model is required")
    return VLMConfig(
        base_url=resolved_base_url,
        api_key=api_key,
        model=resolved_model,
    )


def create_vlm_client(config: VLMConfig) -> Any:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise WorkflowError(
            "The openai package is required; install it before running the workflow"
        ) from exc
    return OpenAI(
        base_url=config.base_url,
        api_key=config.api_key,
        max_retries=0,
    )


def parse_json_response(content: str, expected_type: type | None = None) -> Any:
    if not isinstance(content, str) or not content.strip():
        raise WorkflowError("VLM returned empty or non-text content")

    stripped = content.strip()
    if stripped.startswith("```"):
        match = re.fullmatch(r"```(?:json)?[ \t]*\r?\n([\s\S]*?)\r?\n```", stripped)
        if match is None:
            raise WorkflowError(
                "VLM response must contain only JSON or one complete JSON code block"
            )
        stripped = match.group(1).strip()

    try:
        value = json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise WorkflowError(f"VLM response is not valid JSON: {exc}") from exc

    if expected_type is not None and not isinstance(value, expected_type):
        expected_name = {
            dict: "object",
            list: "array",
        }.get(expected_type, expected_type.__name__)
        raise WorkflowError(f"VLM JSON top level must be a {expected_name}")
    return value


def call_vlm_json(
    client: Any,
    model: str,
    system_prompt: str,
    user_message: str | list[dict[str, Any]],
    expected_type: type | None = None,
    max_tokens: int | None = None,
    raw_response_path: Path | None = None,
    response_metadata_path: Path | None = None,
    json_text_preprocessor: Callable[[str], str] | None = None,
) -> Any:
    request: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    }
    if max_tokens is not None:
        request["max_tokens"] = max_tokens
    try:
        completion = client.chat.completions.create(**request)
        choice = completion.choices[0]
        content = choice.message.content
    except Exception as exc:
        # Provider errors can echo request headers or credentials. Keep the
        # error type/status for diagnosis without exposing the response body.
        status = getattr(exc, "status_code", None)
        detail = f", HTTP {status}" if isinstance(status, int) else ""
        raise WorkflowError(
            f"VLM API call failed ({type(exc).__name__}{detail}); "
            "check the API configuration and service availability"
        ) from None
    if raw_response_path is not None:
        raw_content = content if isinstance(content, str) else repr(content)
        write_text_exclusive(raw_response_path, raw_content)
    if response_metadata_path is not None:
        write_json_exclusive(
            response_metadata_path,
            {"finish_reason": getattr(choice, "finish_reason", None)},
        )
    parse_content = (
        json_text_preprocessor(content)
        if json_text_preprocessor is not None and isinstance(content, str)
        else content
    )
    return parse_json_response(parse_content, expected_type)


def load_prompt(path: Path) -> str:
    try:
        prompt = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise WorkflowError(f"Cannot read system prompt {path}: {exc}") from exc
    if not prompt.strip():
        raise WorkflowError(f"System prompt is empty: {path}")
    return prompt


def ensure_targets_absent(paths: list[Path] | tuple[Path, ...]) -> None:
    existing = [path for path in paths if path.exists()]
    if existing:
        joined = ", ".join(str(path) for path in existing)
        raise WorkflowError(f"Output target already exists: {joined}")


def write_json_exclusive(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    except FileExistsError as exc:
        raise WorkflowError(f"Output target already exists: {path}") from exc
    except OSError as exc:
        raise WorkflowError(f"Cannot write output {path}: {exc}") from exc


def write_text_exclusive(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as handle:
            handle.write(value)
    except FileExistsError as exc:
        raise WorkflowError(f"Output target already exists: {path}") from exc
    except OSError as exc:
        raise WorkflowError(f"Cannot write output {path}: {exc}") from exc


def read_json(path: Path, expected_type: type) -> Any:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise WorkflowError(f"Cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, expected_type):
        raise WorkflowError(f"{path}: expected {expected_type.__name__}")
    return value


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
