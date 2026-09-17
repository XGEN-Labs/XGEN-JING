# Prompt Skills

Generate XGEN-JING inference cases from a story and optional reference images. The
workflow uses a Chat Completions API for text generation and local Python
functions for normalization, compilation and validation. It does not load video
models, and its API dependency is installed separately.

For coding agents, [SKILL.md](SKILL.md) provides the skill entry point and links
to the same workflow. No separate implementation is required.

## Setup

Run from the repository root with Python 3.10 or newer:

```bash
python3 -m pip install -r prompt_skills/requirements.txt
cp prompt_skills/api.env.example prompt_skills/api.env
```

Fill in the local `api.env` file, then load it:

| Variable | Purpose |
| --- | --- |
| `VLM_API_KEY` | API credential; read only from the environment |
| `VLM_BASE_URL` | Chat Completions-compatible service endpoint |
| `VLM_MODEL` | Model name; image inputs require a vision-capable model |

```bash
source prompt_skills/api.env
```

All three values are required. There is no built-in endpoint, key or model.
`--base-url` and `--model` override their environment variables. Local `api.env`
and its backups are ignored by Git; the example contains empty values only.

## Generate and run a case

```bash
python3 -m prompt_skills.workflow.run \
  --case-dir prompt_skills/examples/room \
  --output-dir outputs/prompt_skills/room

bash demo.sh \
  cases=outputs/prompt_skills/room/room_cases_en.json
```

Run `demo.sh` in an inference environment with the H3 components and JING transformer
configured in `configs/bidirection.yaml` or through the `model.h3` and
`model.transformer` command-line overrides.
Both `room_cases.json` and `room_cases_en.json` are directly loadable
cases files. The workflow targets the default `generation.first_chunk_size=2` layout,
24 FPS and four-step inference. Sampler settings belong to the inference runtime,
not to the cases JSON.

A case directory contains `prompt.txt` and an optional `ref/` directory. Images
are sorted by filename and become `<Picture 1>`, `<Picture 2>`, etc. Supported
formats are PNG, JPG/JPEG and WebP. The workflow preserves their order and writes
absolute image paths into the cases. The default demo accepts up to five images.
Without `ref/`, generation uses text only.

Alternative inputs:

```bash
python3 -m prompt_skills.workflow.run \
  --input 'First-person view: enter a quiet study and approach the wooden table.' \
  --base-name study \
  --output-dir outputs/prompt_skills/study

python3 -m prompt_skills.workflow.run \
  --input-file prompt_skills/examples/room/prompt.txt \
  --base-name room \
  --output-dir outputs/prompt_skills/room_text
```

Choose exactly one of `--case-dir`, `--input-file` or `--input`. The output base
name defaults to the directory name or input file stem; literal input requires
`--base-name`. Existing outputs are never overwritten. Use a new directory or
base name for another run.

## Workflow and outputs

| Operation | Output suffix |
| --- | --- |
| Generate a story plan and reference captions | `_story.json` |
| Generate environment descriptions and timed actions | `_environment.json`, `_actions.json` |
| Compile actions into inference cases locally | `_cases.json` |
| Translate narration into English; copy if already English | `_cases_en.json` |

Story and action generation each make one model call. Compilation is local.
English localization makes one call for Chinese narration and no call for English
narration. Dialogue remains in its original language. Story generation also
saves its raw reply and finish reason for debugging.

Validation checks story structure, action timing, dialogue, control lengths,
reference bindings and final compilation. Add `--skip-validation` for debugging
to skip validators and the final audit. Required JSON structure, environment
bindings, normalization, reference integrity and supported control syntax remain
checked.

## Controls

Generated actions and the final cases use the same control format. The keys
`w`, `s`, `a` and `d` mean forward, backward, left and right translation.
The compiler copies each action's `control` list unchanged:

| Control list | Meaning |
| --- | --- |
| `["w", "w"]` | Forward for two slices |
| `["w,a"]` | Forward and left simultaneously for one slice |
| `[""]` | No translation keys for one slice |

List entries are ordered in time. For forward followed by left, generate two
actions using `"w"` and `"a"` respectively, preserving their order and timing.
Each action has one control phase; a comma within a string combines keys for
that slice.

Each chunk has only `prompt`, `repeat` and a `control` list of that length.
Frames equal `17 * sum(repeat) + 5`. Intermediate rendering metadata is omitted
from the final JSON; references, resolution, seed and output name are preserved.

View rotation is expressed in action prose, without mapping it to translation.
In-place turns use no translation keys. Legacy `trajectory` fields, `*` counts,
parenthesized expressions and rotation keys are rejected even with validation
disabled. The intermediate schema is now 6.7; regenerate older intermediate
artifacts. Old trajectory comma expressions describe ordered motions and cannot
be converted by simply removing their counts. Existing final cases already using
`control` lists remain compatible.

## Code layout

```text
prompt_skills/
├── SKILL.md                # Agent instructions
├── README.md
├── api.env.example
├── requirements.txt
├── examples/room/prompt.txt
├── prompts/                # Current story, action and localization prompts
└── workflow/
    ├── run.py              # Single CLI and workflow orchestration
    ├── common.py           # API configuration and JSON/file operations
    ├── generation.py       # Story and action generation
    ├── localization.py     # English narration with unchanged dialogue
    ├── normalize.py        # Story and action normalization
    ├── compiler.py         # Deterministic conversion to inference cases
    ├── references.py       # Image ordering and Picture markers
    ├── audit.py            # Saved provenance and compilation checks
    └── validation/         # Story, action, case and localization rules
```

Only active prompts are included. The intermediate `_pipeline.schema_version`
field identifies the validation contract; it is not a historical prompt revision.
