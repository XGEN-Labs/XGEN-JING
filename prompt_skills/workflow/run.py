"""Run the complete prompt workflow."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from .audit import audit
from .common import (
    VLMConfig,
    WorkflowError,
    create_vlm_client,
    ensure_targets_absent,
    load_config,
)
from .compiler import compile_cases
from .generation import generate_actions, generate_story
from .localization import localize_cases


@dataclass(frozen=True)
class ArtifactPaths:
    story: Path
    environment: Path
    agents: Path
    cases: Path
    english: Path

    def all(self) -> tuple[Path, ...]:
        return self.story, self.environment, self.agents, self.cases, self.english


def validate_base_name(base_name: str) -> str:
    if (
        not base_name
        or base_name in {".", ".."}
        or "/" in base_name
        or "\\" in base_name
        or "\0" in base_name
    ):
        raise WorkflowError(
            "base_name must be one non-empty filename component without path separators"
        )
    return base_name


def build_artifact_paths(output_dir: Path, base_name: str) -> ArtifactPaths:
    safe_name = validate_base_name(base_name)
    return ArtifactPaths(
        story=output_dir / f"{safe_name}_story.json",
        environment=output_dir / f"{safe_name}_environment.json",
        agents=output_dir / f"{safe_name}_actions.json",
        cases=output_dir / f"{safe_name}_cases.json",
        english=output_dir / f"{safe_name}_cases_en.json",
    )


def run_workflow(
    source_input: str,
    base_name: str,
    output_dir: Path,
    config: VLMConfig,
    client: Any | None = None,
    *,
    validate: bool = True,
    reference_images: Sequence[Path] = (),
) -> ArtifactPaths:
    paths = build_artifact_paths(Path(output_dir), base_name)
    ensure_targets_absent(paths.all())
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    active_client = client if client is not None else create_vlm_client(config)

    validation = {"validate": validate}
    status = "PASS" if validate else "DONE (validation skipped)"

    print("[story] Generating plan")
    generate_story(
        active_client,
        config.model,
        source_input,
        base_name,
        paths.story,
        reference_images=reference_images,
        **validation,
    )
    print(f"[story] {status}")

    print("[actions] Generating environments and actions")
    generate_actions(
        active_client,
        config.model,
        paths.story,
        paths.environment,
        paths.agents,
        **validation,
    )
    print(f"[actions] {status}")

    print("[compile] Building inference cases")
    compile_cases(paths.agents, paths.cases, **validation)
    print(f"[compile] {status}")

    print("[english] Localizing narration")
    localize_cases(
        active_client, config.model, paths.cases, paths.english, **validation
    )
    print(f"[english] {status}")

    if validate:
        print("[final] Auditing artifact consistency")
        audit(paths.story, paths.environment, paths.agents, paths.cases, paths.english)
    print(f"Workflow {status}: {output_dir}")
    return paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python3 -m prompt_skills.workflow.run",
        description="Run the prompt workflow with validation after each operation.",
    )
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument(
        "--case-dir",
        type=Path,
        help="Case directory containing prompt.txt and optional ref/ images",
    )
    inputs.add_argument("--input", help="Story description")
    inputs.add_argument(
        "--input-file",
        type=Path,
        help="UTF-8 file containing the story description",
    )
    parser.add_argument(
        "--base-name",
        help="Output name; defaults to case directory name or input file stem; required with --input",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip validators and the final audit; retain parsing and reference checks",
    )
    parser.add_argument(
        "--base-url",
        help="Chat Completions API endpoint; overrides VLM_BASE_URL",
    )
    parser.add_argument(
        "--model",
        help="Model name; overrides VLM_MODEL",
    )
    return parser


def _resolve_input(args: argparse.Namespace) -> tuple[str, str]:
    if args.input is not None:
        if args.base_name is None:
            raise WorkflowError("--base-name is required when using --input")
        return args.input, validate_base_name(args.base_name)

    input_file: Path = (
        args.case_dir / "prompt.txt" if args.case_dir else args.input_file
    )
    try:
        source_input = input_file.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise WorkflowError(f"Cannot read input file {input_file}: {exc}") from exc
    base_name = (
        args.base_name
        if args.base_name is not None
        else (args.case_dir.name if args.case_dir else input_file.stem)
    )
    return source_input, validate_base_name(base_name)


def _reference_images(case_dir: Path | None) -> list[Path]:
    if case_dir is None or not (case_dir / "ref").is_dir():
        return []
    return sorted(
        path
        for path in (case_dir / "ref").iterdir()
        if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        source_input, base_name = _resolve_input(args)
        config = load_config(base_url=args.base_url, model=args.model)
        run_workflow(
            source_input=source_input,
            base_name=base_name,
            output_dir=args.output_dir,
            config=config,
            validate=not args.skip_validation,
            reference_images=_reference_images(args.case_dir),
        )
    except (WorkflowError, ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
