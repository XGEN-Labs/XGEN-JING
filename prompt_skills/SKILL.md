---
name: jing-prompt-skills
description: Turn a story and optional reference images into validated XGEN-JING video inference cases with timed prompts and WASD controls. Use when preparing or revising cases for the XGEN-JING demo.
---

# XGEN-JING Prompt Skills

Use the bundled workflow to produce a cases JSON that the XGEN-JING demo can load.
Read [README.md](README.md) for API setup, input options and output paths. Run
commands from the repository root, which contains `demo.sh` and `prompt_skills/`.

```bash
python3 -m prompt_skills.workflow.run \
  --case-dir path/to/case \
  --output-dir outputs/prompt_skills/case
```

A case directory contains `prompt.txt` and optional `ref/` images. The workflow
reads API credentials from the environment. Use a new output directory for a
revision; existing artifacts are not overwritten. Keep validation enabled for
cases intended for inference. Report a failed stage before attempting a new run.

The final `*_cases_en.json` is the English cases file. Preserve dialogue in
its original language, reference image order, `<Picture N>` bindings, timing and
control arrays. Each chunk's `control` list must have `repeat` entries, using
WASD combinations such as `"w,a"` or `""` for no translation. Describe view
rotation in the prompt; it has no control key in the demo.

The compiler targets 24 FPS with `generation.first_chunk_size=2` and computes
`num_frames = 17 * sum(repeat) + 5`. Inference settings such as the four-step
sampler belong in the demo configuration, not the cases JSON. Return the
validated cases path; run video inference when requested by the user.

When changing generation behavior, edit the relevant prompt:

- [prompts/story.md](prompts/story.md): story, roles and spatial planning.
- [prompts/actions.md](prompts/actions.md): timed actions and control schedules.
- [prompts/english.md](prompts/english.md): English narration and dialogue preservation.

Keep schema changes consistent with the compiler and validators in `workflow/`.
