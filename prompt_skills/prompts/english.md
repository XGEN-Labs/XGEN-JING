# Jing English Localization

## Input and output

Translate narration in the supplied cases JSON into English while preserving all non-prompt data and original-language dialogue.

The user message supplies exactly one validated Chinese H3 Official JSON document. Produce exactly the English H3 Official JSON document and no prose wrapper. The caller saves it as the separate `_en.json` sibling and validates it against the Chinese source. This API transport rule takes precedence over any retained file-writing, saved-path reporting, or stop/report mechanics.

This execution permits one OpenAI API call. A validation failure terminates this execution; do not assume an automatic repair call.

# Translation rules

The sole case-data input is the newly persisted `<base>_cases.json`. Do not read raw input, Story Decision, Environment Intermediate, Agents Intermediate, neighboring cases, hidden notes, or remembered earlier-stage details.

Create a separate sibling `<base>_cases_en.json`; never overwrite the source cases. Translate every natural-language portion of each `chunks[].prompt` except the complete dialogue blocks inside `<d>...</d>`, which must remain byte-for-byte unchanged. Translate `overall_soundscape`. Preserve event meaning, action and chunk order, directions, identities, object state and ownership, S-role bindings, dialogue text and language labels, audio cues, and terminal proof.

Only prompt text and the prescribed filename may change. Use the exact English POV opening, preserve every complete `<d>...</d>` dialogue block including its original language label and spoken text, insert `_en` before `.mp4` in `save_name`, preserve every other non-prompt value exactly, and leave no Chinese text outside preserved dialogue blocks in the English artifact. This is localization, not story repair, prompt refinement, summarization, or embellishment.

If the source H3 lacks information or contains an upstream defect, stop and return it to the owning stage. Never silently repair the source during translation.

# Localization contract

English localization converts the validated Chinese H3 Official artifact into a separate English H3 Official artifact. It is a lossless semantic localization stage, not another story, staging, or compilation stage.

## Input boundary

The sole case-data input is:

```text
<base>_cases.json
```

Do not read the raw narrative, Story Decision, Environment Intermediate, Agents Intermediate, a prior English version, neighboring cases, hidden notes, or remembered earlier-stage details. General language knowledge and this format contract are allowed; other case artifacts are not.

If the source H3 is invalid or lacks information needed for a faithful translation, stop. Route the defect to its owning stage, regenerate the Chinese H3, and restart English localization from that new file. Do not fill gaps from an earlier artifact.

## Output and naming

Write a new sibling file:

```text
<base>_cases_en.json
```

Never overwrite, rename, or mutate the source H3. For every case, insert `_en` immediately before the final `.mp4` in `save_name`:

```text
room.mp4 -> room_en.mp4
```

Do not add a second `_en` suffix. English localization always starts from the unsuffixed Compilation artifact, never from a prior English localization output.

## Fields that may change

Only these values may differ from Compilation:

- each case's `save_name`, solely by the required `_en` suffix;
- each `chunks[].prompt`, solely through faithful English localization.

Preserve exactly:

- top-level array length and case order;
- all object keys and nesting;
- chunk count and chunk order;
- `seed`, dimensions, frame count, inference steps, controls, and every other case value;
- `repeat`, `control` lists, and every other non-prompt chunk value;
- all S identifiers and their per-chunk occurrences;
- the number and placement by chunk of dialogue blocks.

Unknown metadata is preserved unchanged. Do not delete a field merely because the usual H3 envelope does not require it.

## Prompt localization

Translate all natural-language content, including:

- visible action and appearance descriptions;
- camera-wearer movement, facing, and stopping states;
- participant identities, poses, gestures, and voice traits;
- object identity, ownership, support, manipulation, and state;
- spatial anchors, left/right/front/back relations, approach paths, turns, and threshold crossings;
- all prose surrounding dialogue inside `<d>...</d>`; the complete dialogue blocks themselves are copied byte-for-byte and are not translated;
- `overall_soundscape` content;
- non-`N/A` music descriptions when explicitly present.

Use the exact English opening:

```text
First-person POV. integrated_multimodal_description: [Shot 1] Live-action, cinematic.
```

Keep the two ASCII section labels and their order unchanged:

```text
overall_soundscape:

non_diegetic_music:
```

Copy every complete dialogue block from `<d>` through `</d>` byte-for-byte. Do not translate the spoken line and do not change its `[Chinese]` or `[English]` language label. Translate the surrounding speaker declaration and use `Current speaker:` for the English speaker declaration required by the H3 Official contract.

Use `I (S1)` or `my (S1)` for the camera wearer in every chunk. Keep `S1`, `S2`, and later IDs bound to the same participants. Produce fully English prompt prose outside dialogue blocks. Chinese characters and `[Chinese]` labels may remain only inside dialogue blocks copied byte-for-byte from the source.

## Fidelity rules

Preserve what happens, not Chinese word order. English should be natural and generation-ready, but it must not introduce semantic drift.

Do not:

- add, remove, merge, split, or reorder events or chunks;
- repair motivation, continuity, ownership, timing, or causality;
- add visual details, sound cues, dialogue, gestures, camera motion, or consequences;
- weaken or strengthen spatial relations, quantities, certainty, or completion states;
- convert visible action into audio-only information or the reverse;
- summarize repeated continuity anchors when their repetition preserves generation stability;
- change `non_diegetic_music: N/A`;
- translate identifiers, field names, control strings, filenames other than the required suffix, or technical values.

Use stable English terms for recurring participants, places, and objects across every chunk. Preserve explicit phrases such as `no subtitles` and `no camera cut` when present. Maintain the source distinction between what is visible now, what remains behind the camera wearer, and what has not yet entered reach.

## Validation

The validator checks both files as H3 Official, the output filename conventions, absence of Chinese text outside dialogue blocks, case/chunk/key preservation, equality of every non-prompt value, byte-for-byte equality of every complete dialogue block, and per-chunk S-marker preservation. It cannot prove full translation fidelity; review meaning, spatial continuity, terminology, and all non-dialogue prompt content directly against the source H3 before declaring completion.

## Preserve reference-image identifiers

Repeated image references across chunks are intentional. Translate every chunk independently for reference preservation: never remove a scene reference from a middle chunk as redundant, shorten it to "the same place", or move it to another chunk. Preserve each label's occurrence count and its binding to the corresponding scene, person, or object within that chunk.

`<Picture 1>`, `<Picture 2>`, etc. are literal references to the visual inputs, not prose to translate and not dialogue markup. Preserve each exact `<Picture N>` label and its subject/scene association in the same chunk. Never translate, remove, renumber, or replace these references with a caption. For example, translate "<Picture 2>中的青年走向<Picture 1>中的商店" as "the young man in <Picture 2> walks toward the shop shown in <Picture 1>". Add no picture references that are absent from the source. The downstream encoder inserts the actual visual tokens; output only the existing H3 JSON with these references retained in its prompt text.
