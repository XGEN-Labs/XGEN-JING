# Jing Action Planning

## Input and output

Expand the supplied story into environment descriptions and timed first-person actions. Return only the JSON response described below.

The user message supplies exactly one validated Story Decision JSON object. Produce exactly one JSON response envelope with exactly two keys: `environment_intermediate` and `agents_intermediate`. Build Environment first, then Agents from the Story Decision and that Environment. Keep the template's 64-character zero provenance placeholders; after the response, the caller splits the envelope, stamps real hashes, and runs the validators. This API transport rule takes precedence over any retained separate-file, saved-path reporting, or stop/report mechanics.

This execution permits one OpenAI API call. A validation failure terminates this execution; do not assume an automatic repair call.

## Mandatory validator-aligned final gate

Before returning the JSON envelope, enforce all of the following without omitting or weakening any later rule:

**遗漏台词就是不合格。任何一个 action 遗漏其引用台词的全部或部分原文，整条样本即判定为 FAIL，不能作为合格结果输出。必须在对应的 `action_description` 中补全原始台词；意思相同、概括转述或只在其他字段保留台词均不合格。这是硬性失败条件，不是 warning。**

- Every NPC object contains a nonempty `voice`. For an NPC that speaks, use the same stable voice wording in its object, root dialogue, and action description. For a non-speaking NPC, use an explicit non-speaking voice description.
- Every English `action_description` explicitly contains `I` or `my`; every Chinese `action_description` explicitly contains `我`. The exact required First-person POV opening remains unchanged.
- Every nonempty `dialogue_refs` array copies one complete string byte-for-byte from root `action.supporting_dialogue`, including speaker, voice, speech verb, and quoted words. English dialogue uses straight double quotes and Chinese dialogue uses `“...”`.
- Hard failure / 不合格: for every nonempty `dialogue_refs`, copy every referenced quoted utterance verbatim into the SAME action's `action_description`, enclosed in the required quotation marks. Preserve its language, wording, punctuation, and symbols. A summary such as “问出问题”, “等待回应”, or “ask my question” is not a substitute for the actual line. Apply the dialogue-copy gate below before returning JSON.
- Every NPC `prompt_reference` is copied with exactly the same spelling and capitalization everywhere it appears in action descriptions.
- Compute every action's allocated repeat count with the Repeat schedule formula below. Its `control` length equals that allocation exactly, and all entries inside one action are identical. Any retained illustrative mixed schedule is subordinate to this uniform camera-phase gate.

## Environment and action planning

The sole prior-stage case input is a validated `<base>_story.json`. Do not inspect raw narrative, source H3, neighboring cases, hidden notes, or remembered Story generation details. Within this stage, Agents may also consume the Environment created immediately before it.

Story generation beat `action_type` values are descriptive hints and may include `dialogue`, `observation`, `interaction`, `waiting`, or mixed labels. Do not copy these labels into Agents actions. Classify each generated action from its actual plan and camera movement using only `navigation` or `manipulation`: camera travel is navigation; stationary dialogue, observation, waiting, and hand actions are manipulation. For mixed beats, preserve the intended event and physical route while producing actions consistent with their controls.

## Build in order

1. Create `<base>_environment.json` using the embedded Environment Intermediate JSON template below. Assign stable environment IDs and serialize every environment fact Agents needs.
2. Create `<base>_actions.json` using the embedded Agents Intermediate JSON template below and only Story Decision plus the new Environment.
3. Make Agents self-contained for Compilation: include render configuration, stable participant prompt references, speaker IDs, timestamps, complete action descriptions, per-action soundscapes, terminal result, and a per-repeat discrete control schedule for every action.
4. Use `""` for every stationary Ego/S1 repeat, including repeats where only an NPC moves.
5. Apply both continuity references to every action description. Resolve actor/hand binding, visibility, physical order, occupancy, transfer of control, camera pose, view cone, reach, route, and direction frame here.

## Camera-phase gate

Each action represents one semantic camera-control phase and all entries in its control schedule must be identical. Split an action whenever control changes between turn, translation, settle, or another phase. A stationary phase must describe only the terminal state, preserve landmark identity, scale, screen position, and lighting, and explicitly forbid replay, motion, zoom, and scene change.

## Stamp and validate

Do not edit Environment after stamping without stamping both Action generation artifacts again.

Stop after Action generation. Compilation receives only the persisted Agents Intermediate. If the story decision itself is wrong, return ownership to Story generation instead of compensating here.

## Environment schema

Environment Intermediate is the first substep of Action generation. It is generated only from Story Decision.

```json
{
  "_pipeline": {
    "schema_version": "6.7",
    "stage": 2,
    "story_decision_sha256": "<64 lowercase hex>"
  },
  "environments": [
    {
      "environment_id": "<string>",
      "content": "<complete static environment description>"
    }
  ]
}
```

Each physical continuous space has one stable ID. `content` describes only static place type, layout, surfaces, fixed anchors, boundaries, light, weather, visibility, and persistent ambience.

Do not write actions, timestamps, dialogue, participants' changing poses, camera-induced motion, ownership changes, or terminal outcomes here. Those belong in Agents.

Environment IDs must exactly match Story generation `environment_requirements`. The caller stamps provenance after semantic authoring.

## Action schema

The action document is the sole case-data input to compilation. It must contain all narrative and rendering data needed to build inference cases.

## Required shape

```json
{
  "_pipeline": {
    "schema_version": "6.7",
    "stage": 2,
    "story_decision_sha256": "<64 lowercase hex>",
    "environment_sha256": "<64 lowercase hex>"
  },
  "render_config": {
    "save_name": "<basename>.mp4",
    "seed": 10001,
    "height": 544,
    "width": 960,
    "fps": 24,
    "num_inference_steps": 4,
    "control_signal": "camera_delta",
    "discrete_camera": true,
    "prompt_language": "Chinese | English",
    "visual_style": "<string>",
    "non_diegetic_music": "N/A"
  },
  "intent": {
    "goal": "<string>",
    "scene_change": false,
    "start_environment_id": "<environment_id>",
    "end_environment_id": "<environment_id>"
  },
  "action": {
    "instruction": "<string>",
    "supporting_dialogue": ["<speaker, voice, and exact quoted words>"]
  },
  "agents": {
    "npcs": [
      {
        "agent_id": "<string>",
        "identity": "<string>",
        "prompt_reference": "<stable natural reference used verbatim in action descriptions>",
        "voice": "<stable voice description>",
        "interaction_mode": "<string>",
        "state_description": "<string>"
      }
    ],
    "ego": {
      "agent_id": "<string>",
      "identity": "<string>",
      "prompt_reference": "<stable natural reference for speaker declaration>",
      "voice": "<stable voice description>",
      "action_list": {
        "total_num": 1,
        "actions": [
          {
            "action_id": 1,
            "timestamp": "00:00.0-00:03.0",
            "action_type": "navigation | manipulation",
            "action_plan": "<string>",
            "speaker_agent_id": null,
            "dialogue_refs": [],
            "scene_dynamics": [
              {
                "environment_id": "<environment_id>",
                "description": "<string naming its environment_id>"
              }
            ],
            "action_description": "<complete First-person POV prompt body without S markers or H3 envelope>",
            "overall_soundscape": "<diegetic sound derived during Action generation>",
            "control": ["w", "w", "w", "w"]
          }
        ]
      }
    }
  }
}
```

## Compilation packaging requirements

- `render_config` is complete; Compilation may not fetch defaults elsewhere. This pipeline requires `control_signal: "camera_delta"` and `discrete_camera: true`.
- `prompt_reference` is unique, natural language, contains no S marker, and appears verbatim wherever that NPC is referenced in an action description.
- `speaker_agent_id` is `null` when `dialogue_refs` is empty. With one dialogue ref, it names Ego or one NPC and is the only speaker in that action.
- `action_description` begins exactly with `第一人称POV` for Chinese or `First-person POV.` for English.
- It contains no S/O/B labels, H3 envelope, `<d>` wrapper, soundscape section, or non-diegetic section.
- `overall_soundscape` is complete for its action. Compilation copies it without consulting Environment.
- Every action has a nonempty `control` array with one entry per allocated repeat. Each entry is either the string `""` for a stationary atomic repeat or a canonical discrete control string using lowercase `w/s/a/d`. JSON `null` is invalid in this array.
- `control` describes only the unique first-person camera wearer, Ego/S1. Never add it to an NPC or use it to encode NPC locomotion, pose, gestures, or turns. NPC motion belongs in `action_description` and `scene_dynamics`. If an NPC moves while Ego remains planted, use `""` for every corresponding Ego control entry.
- `w/s/a/d` translate forward/back/left/right. Use bare lowercase keys; do not use repetition expressions. View rotation is described in the action prompt, with `""` when there is no translation; do not generate rotation keys.
- Comma-separated keys in one array entry are simultaneous: `w,a` means moving diagonally forward-left, not walking forward and then left.
- Compilation emits one chunk per action, with `repeat` equal to its control length and an equally long `control` array. It copies the control array unchanged. Action generation and the final cases use the same control syntax.

## Repeat schedule

Derive the total repeat budget from the final action timestamp `T` and FPS `F`:

```text
R = nearest positive integer to (F * T - 5) / 17
```

Allocate `R` across actions in proportion to timestamp duration, giving every action at least one repeat and assigning remaining repeats by largest fractional remainder. The length of each action's `control` array must exactly equal that action's allocation. The validator reports the expected length when it differs.

For an action allocated six repeats, this schedule:

```json
"control": ["w", "w", "w", "w", "w", "w"]
```

compiles to one H3 chunk:

```json
[
  {"repeat": 6, "control": ["w", "w", "w", "w", "w", "w"]}
]
```

The chunk receives the compiled prompt and soundscape from its owning action.

## Narrative and continuity requirements

While authoring every `action_description`, apply both first-person spatial continuity and first-person embodied action consistency. The former governs camera pose, view cone, reach, routes, and direction frames; the latter governs actor-to-hand binding, visibility transitions, occupancy, physical order, and object-control transfer. Unresolved blocking embodied-action defects make Agents incomplete and must be repaired before Compilation.

Every action has one coherent ordered stage and inherits the prior ending camera pose, participant positions, view cone, object supports, reachability, open routes, and information state. Ordered Ego translation, a stationary interval, and later Ego translation require separate actions even when they form one causal stage. An NPC action or speaking turn may share an action only while its Ego camera controls remain unchanged. Do not describe sequential phases as simultaneous. Split different speakers, ambiguous ordering, and competing ownership changes into separate actions. Preserve handoff support as giver-only → shared → receiver-only. End with visible physical or social proof.

Actions use sequential IDs, continuous positive timestamps, declared environment IDs, exact root dialogue references, synchronized `total_num`, and control schedules whose lengths match the deterministic repeat allocation. The final timestamp is the target duration used by Compilation repeat allocation.

# First-person spatial continuity during generation

Apply this reference while generating every action and H3 chunk, not only as a final review. It covers POV movement, turns, reaching, pickup, handoff, route clearing, entrances, exits, and directional language.

Pair it with first-person embodied action consistency while Action generation authors each `action_description`. This reference owns camera pose, view cone, reach, routes, direction frames, and a pointing gesture's visible endpoint. The paired reference owns actor-to-hand binding, hand state, occupancy, contact, release, and object-control transfer. An action must satisfy both before Compilation.

## Spatial state carried between actions

Before writing action N, inherit action N-1's ending state:

```text
camera position + facing + visible cone
participant positions + facings
object support/holder + visible location
reachable targets + open routes + obstacles
```

After writing action N, update this state explicitly. Action N+1 must begin from the updated state.

Keep three frames separate:

- **World:** stable landmarks such as bench, road, doorway, aisle, curb, or counter.
- **Observer:** left, right, ahead, and behind relative to the camera's current pose.
- **Object/body:** a bench's right half, a vehicle's left side, or a person's left hand.

After any camera turn or movement, recompute observer-relative directions. If pose does not support a direction, use a stable world/object anchor instead of guessing.

## Generation checks for each action

1. Is the target inside the current view cone? If not, turn first.
2. Is it within reach? If not, approach first.
3. Is there a clear route consistent with prior positions?
4. Which reference frame owns each direction word?
5. What supports or holds each important object before and after the action?
6. Does the ending pose and state exactly support the next action?

Looking down cannot reveal the rear view. Bending cannot replace closing lateral distance. A bare side-step does not prove a doorway or aisle has been cleared.

For pickup, preserve `surface → grasp/contact → hand`. For handoff, preserve `giver only → giver + receiver → receiver only`.

## Pointing geometry and hand-actor binding

Apply this section only when an action contains an explicit pointing or directional hand gesture. Treat the gesture as a spatial constraint, not as decorative motion.

Before writing the action, resolve this record internally:

```text
gesture actor + attached arm/sleeve + visible target landmark
+ target's current screen sector + fingertip endpoint
+ subsequent camera turn or travel direction + all inactive hands
```

### Bind the gesture to its referent

- Keep the actor and the referenced landmark visible in the same viewing cone. Establish the landmark's current screen sector before describing the hand motion.
- Make the shoulder-to-wrist-to-fingertip ray terminate visually on the landmark or its entrance. The ray must agree with the camera's subsequent turn or travel direction; a route straight ahead must not be indicated by a hand aimed at a side wall or upward into empty space.
- Keep body-relative laterality separate from screen direction. A front-facing person's anatomical right and the image's right are not interchangeable. Omit `left hand` or `right hand` when anatomy is not story-critical; constrain the visible screen direction and fingertip endpoint instead.
- End the gesture beat with the target and fingertip alignment still readable. Begin the next beat from the same geometry: the actor lowers the hand, then Ego turns toward or moves along the indicated route. Do not silently replace the indicated target with a different route.

### Bind the gesture to exactly one actor

- Name the sole gesture actor as the grammatical subject and keep the visible hand anatomically connected through wrist, sleeve, elbow, and shoulder to that actor. Attach glove or sleeve attributes to the same arm, not to a detached hand entering from an image edge.
- State the inactive-hand condition in the same action: when an NPC points, Ego's hands remain fully below or outside the frame and do not point, reach, or mirror; every other participant keeps both hands neutral. Apply the inverse when Ego alone is the intended gesture actor.
- Never render an NPC point and an Ego point simultaneously unless the story explicitly requires two separate gestures. Looking at or visually confirming an indicated target is camera attention, not an Ego hand action; describe the held view instead of saying that Ego physically follows or echoes the gesture.
- Keep one pointing arm and one referenced target as the dominant visible change. Do not combine the point with object handling, a second person's gesture, or the start of travel in the same action.

Use a prompt shape like this, adapted to the actual geometry:

```text
The glass-corridor entrance is already visible on the image right. The restorer remains on the image left and extends one sleeve-connected arm horizontally toward the image right; his fingertip aligns with the corridor entrance. He is the only person gesturing. Ego's hands remain fully out of frame, and the other participant's hands remain lowered.
```

Reject or rewrite the action if the fingertip endpoint, referenced landmark, next travel direction, gesture actor, or inactive-hand state cannot all be determined from the prompt alone.

## Concrete case: bus-stop red-scarf return

Stable anchors: the bench is parallel to the road; the boarding marker is on the road side of the bench; the bus door opens toward the platform; S1 starts beside the bench's left end; S2 sits on its right half; the scarf starts on S2's bag handle.

```text
t0 S1 by left end; S2 on right half; scarf on bag
t1 S2 walks to door; scarf falls on her vacated seat
t2 S1 calls from bench; S2 turns at boarding marker
t3 S1 turns to bench, steps along it, bends, and picks up scarf
t4 S1 follows S2's short path; they hand off scarf at marker
t5 S1 moves to bench side outside door lane; S2 boards
t6 S1 turns back along the path and sees the empty seat
```

### Failure: bending replaces approaching

Unsupported: S1 stands at the bench's left end and directly bends to take a scarf from the right half.

Repair: S1 turns toward the bench, steps along it toward S2's vacated seat, then bends and reaches.

### Failure: an old ego direction survives a turn

Unsupported: after facing S2 and turning down to the bench, the bus door is still called “right-front.”

Repair: call it “the bus door waiting beside the curb and opening toward the platform.”

### Failure: a side-step claims to clear the route

Unsupported: “S1 steps left to make room.”

Repair: “S1 steps toward the bench side and away from the door lane, leaving a clear path from S2 to the bus door.”

### Failure: pitch reveals something behind

Unsupported: “S1 lowers his gaze to the bench behind and left.”

Repair: “S1 turns his head back along the path he just walked, then settles his gaze on S2's vacated seat.” The unsupported ego-left claim is removed.

### Scarf support chain

```text
bag handle → bench seat → S1 right hand
→ S1 right hand + S2 left hand → S2 left hand
→ S2 neck/coat collar
```

Do not proceed to the next action while view, reach, route, reference frame, or support is unresolved. Mark insufficient geometry for review instead of inventing a direction.

# First-person embodied action consistency during generation

Apply this reference while Action generation authors and revises every
`action_description`. Pair it with
first-person spatial continuity: that
reference owns camera pose, view cone, reach, routes, direction frames, and a
pointing gesture's visible endpoint; this reference owns actor-to-hand binding,
hand state, occupancy, contact, release, and object-control transfer.

Story generation decides the intended action beats and object support chains. Action generation
must realize them as physically executable first-person action text. Compilation
preserves that text and must never repair an embodied-action defect.

## Track hand state before writing prose

Internally track each action-relevant hand for Ego and every visible NPC. Use
anatomical left/right only when the case establishes it reliably; otherwise
use a stable anonymous hand internally and write `one hand` in the prompt.

Use this state vocabulary:

```text
out_of_frame
visible_empty
reaching
touching
grasping(object)
holding(object)
releasing(object)
```

Inherit each hand's state from the prior action, apply only visible and ordered
transitions, then carry the resulting state into the next action. A normal
manipulation path is:

```text
out_of_frame -> visible_empty -> reaching -> touching
-> grasping(object) -> holding(object) -> releasing(object)
-> visible_empty or out_of_frame
```

The ledger is generation-time reasoning only. Do not add it, scores, error
tags, or review metadata to Agents or H3.

## Per-action consistency checks

Review every action using R1-R10. R1, R2, R4, R5, and R6 are blocking: if any
remains unresolved, revise or split the Action generation action before compilation.

### R1 — Actor and hand binding (blocking)

Make every active hand belong unambiguously to Ego or one named NPC. A lower
foreground hand connected to a first-person forearm belongs to Ego; an NPC hand
must remain visibly connected through wrist, sleeve, elbow, and shoulder to that
NPC. Do not use a detached `a hand appears` construction when actor identity
matters.

### R2 — Visibility continuity (blocking)

A hand inherited as `out_of_frame` must visibly enter before it points,
reaches, grasps, or releases. Replace an unsupported jump such as `the NPC's
hands are not visible; the NPC points` with a transition such as `the NPC raises
one hand into view and points`.

`Keeps both hands in the pockets throughout` followed by a hand action is a
direct contradiction. Remove `throughout` and show the hand leaving the pocket,
or remove the later hand action.

### R3 — Reliable laterality

Do not infer anatomical left/right from image-left/image-right. A person facing
the camera may have the right hand on the image left. Preserve a previously
established anatomical side when reliable; otherwise write `one hand` and use
screen direction only for spatial geometry.

### R4 — Physical action order (blocking)

Preserve the necessary order of contact and support:

```text
approach -> reach -> touch -> grasp -> move -> establish new support -> release
```

Use `lifts` or `picks up` only after the object leaves its prior support. Use
`places` only after the object reaches a new support and the actor releases it.

### R5 — Hand occupancy (blocking)

One hand cannot perform mutually exclusive actions at the same time. A hand
holding a box cannot also point, open a door, or grasp another object. Use the
other free hand, place the held object down, or show an explicit hand-to-hand
transfer before the new action.

### R6 — Interaction direction and control (blocking)

Name giver, receiver, object, and the moment control transfers. For a central
handoff preserve:

```text
giver holds -> giver presents -> receiver reaches and grasps
-> receiver establishes stable support -> giver releases
-> receiver alone supports the object
```

Do not swap giver and receiver, let the giver release before the receiver is
stable, or leave the terminal holder ambiguous.

### R7 — Evidence-aligned verbs

Use the strongest verb justified by the visible state and no stronger:

```text
reaches toward -> touches -> grasps -> lifts from the support
```

When completion is not established, use `moves toward`, `reaches toward`, or
`begins to` instead of asserting a completed pickup, placement, or transfer.

### R8 — Ego hand state

When an NPC gesture or manipulation could be confused with a first-person
foreground hand, state whether Ego's hands remain out of frame, stay still,
hold an object, or participate. Do not add a POV hand merely to acknowledge an
NPC gesture. For pointing target geometry and subsequent travel direction,
apply the paired spatial-continuity reference.

### R9 — Spatial and object-state result

State the relevant source, target, support, and visible result of a manipulation.
`Moves the cup` is insufficient when ownership or placement matters; specify
where the cup starts, where it moves, and what or who supports it afterward.

### R10 — Atomic and independent clarity

Use explicit actors and objects instead of ambiguous pronouns. Give each action
one dominant semantic change and order compatible supporting motions. Split
competing speakers, ownership changes, or hand tasks, but do not fragment a
simple manipulation into unnecessary finger-level actions.

## High-risk prompt patterns

### NPC hand entering the foreground

Bind the complete body chain and exclude a competing POV hand when necessary:

```text
The NPC extends one sleeve-connected arm from the shoulder. The hand enters
the foreground and reaches toward the cup. Ego's hands remain out of frame.
```

### Pickup and placement

Keep support changes visible:

```text
The hand reaches the cup, closes around it, and lifts it clear of the table.
The hand lowers the cup onto the tray, waits until the tray supports it, then
releases and withdraws.
```

### Reusing an occupied hand

Choose one explicit repair:

```text
Ego holds the box with one hand and points with the other.
Ego places the box down, frees the holding hand, and then points.
Ego transfers the box to the other hand, then points with the freed hand.
```

## Action validation

Before stamping Action generation provenance:

1. Identify every active actor, hand, and manipulated object.
2. Inherit hand occupancy and object support from the prior action.
3. Verify every hand entry, contact, grasp, support transfer, and release.
4. Remove unsupported laterality and downgrade verbs that exceed the evidence.
5. Make Ego's hand state explicit where foreground actor binding could drift.
6. Carry the terminal hand and object states into the next action.
7. Confirm the action also passes first-person spatial continuity.

If intended story logic makes a blocking check impossible, return to Story generation
and repair the beat or support chain. If only the action realization is wrong,
revise Action generation. Never patch the compiled H3 to compensate.

# H3 observed behavior and prompt design

Use this reference when designing or reviewing any H3 case. These rules come from reviewing 70 generated videos, with dense transition checks on representative routine, handoff, following, hazard, and chase cases.

## What the model reliably does

- It usually renders one dominant visual state per high-level prompt chunk.
- It handles a single clear subject moving along one clear route better than a multi-person action chain.
- It preserves broad room identity, large surfaces, lighting, and a centered character more reliably than exact object ownership or fine hand contact.
- Camera controls can influence viewpoint motion, but response was inconsistent across reviewed outputs; newly adding controls did not reliably rescue an over-fragmented prompt.
- It often holds a visually strong composition for most of a chunk, even when the prompt contains several ordered verbs.

## Common observed failures

- A long establishing description becomes several seconds of a nearly static empty room.
- A person named after the opening chunk appears abruptly instead of entering or being approached.
- Prose-only camera movement becomes a hard scene re-composition at the next chunk.
- A complex handoff collapses into the object already being held, changes the object's shape, or omits the giver's release.
- A prompt containing `turn → walk → stop → look down → climb` renders only one endpoint or skips directly to the next location.
- Dialogue-heavy chunks become static character portraits.
- Repeating full appearance descriptions makes the model reset the person instead of continuing the action.
- A destination introduced only in a later chunk looks like a new scene rather than a reached location.
- The final chunk often holds a static target; it does not prove that the travel or operation occurred.

## Design for one dominant semantic phase

Give every chunk one primary semantic phase. Secondary behavior may support it but must not compete with it. Do not equate this with one microscopic action per chunk: generated review showed that thirteen short prompts in a 22-second case collapsed into about four unrelated compositions and skipped most intended actions.

Good primary changes include:

- empty route → person enters or becomes visibly closer;
- person working → person turns in place to acknowledge the camera;
- object with giver → object extended between both parties;
- shared grip → object fully owned by receiver;
- facing person → turn completes with route centered;
- far doorway → doorway grows and stops at the threshold;
- top of ladder → viewpoint lowers rung by rung to the floor;
- normal walk → alarm triggers a visibly faster gait.

Split when a beat combines major changes in location, object ownership, facing, and goal. Keep small supporting motions together when separating them would create a sequence of one- or two-second semantic prompts. For a 19–24 second case, start with about five to seven meaningful phases and exceed that only when the source truly contains more independently readable events.

## Put action before decoration

Start a moving chunk with the inherited state and primary action. Add only the environmental anchors needed to constrain that action.

Prefer:

`第一人称POV停在控制台前。男人原地转身面对镜头，身旁仍是闪烁的显示器。`

Avoid beginning with a long inventory of the whole room and placing the turn or walk at the end. The model commonly spends the chunk rendering the inventory and ignores the late action.

## Do not import invisible prehistory

If the camera begins already beside a worker, the worker cannot react to footsteps from an approach that the video never showed. Use one of two coherent openings:

- show the camera approaching, then let the worker hear or see that approach; or
- begin stationary, let the camera wearer greet or knock, then let the worker react in place.

Keep trigger and response in visible chronological order. Avoid using an omitted prior action as an invisible cause merely to make a static opening feel connected.

## Maintain active-subject continuity

- Introduce every important person in the first chunk where that person's location affects the action.
- Begin the next chunk with the same person, pose, distance, and active object before adding a new action.
- Use a short stable identity signature rather than repeating a full portrait.
- If a person must leave view, make the camera turn or the person cross an image edge as the primary state change.
- Do not expect `the same person` or a name alone to preserve appearance after a large re-composition.

## Treat high-difficulty interactions conservatively

Hand contact, object transfer, doors, ladders, readable text, and simultaneous gestures are fragile.

- Use one plain object and one giver-receiver pair.
- Split `pick up`, `extend`, `shared grip`, `release`, and `use` when the transfer is central.
- If the transfer is not central, show the giver extend the object, then begin the next chunk with the receiver already holding it; do not spend duration on unstable shared contact.
- Never combine putting on equipment with turning away and walking.
- Keep doors and ladders centered before interaction; do not require a large turn during the same beat.
- Avoid precise finger positions, small labels, buttons, connectors, or readable interfaces unless indispensable.

## Keep visible action density

- Do not allocate a long opening chunk only to a static establishing view. Establish the route while a person walks, a worker performs a simple task, an animal enters, or another goal-relevant change occurs.
- A stationary dialogue chunk may be visually stable, but the adjacent chunks should contain a visible approach, gesture, handoff, turn, or departure.
- Do not fill time by repeating a static pose. If the action load is low, shorten the case or add only a motivated response or consequence.
- End on an observable completion: object ownership changed, threshold crossed, target reached at close range, machine operated, hazard avoided, or route choice begun.

## Choose embodied motion by causal evidence

- Routine indoor tasks: restrained head motion and normal walking.
- Ordinary outdoor paths: mild step rhythm adjusted to surface.
- Mud, rain, snow, loose ground, darkness, or clutter: slower steps, shorter stride, task-driven downward glances, and small balance corrections.
- Suspense without pursuit: cautious advance, listening stops, and turns caused by sounds or occlusion.
- Chase, escape, emergency, or visible imminent hazard: faster gait, stronger periodic body motion, shorter pauses, and abrupt but motivated turns.
- Never add random shake from a genre label alone. Require a threat, alarm, impact, loss of footing, running action, wind exposure, or another bodily cause.

## Archetype checks

### Asking directions

Show a credible information gap, approach a credible helper, stop, ask, receive one clear gesture, turn toward that direction, and begin moving. Do not keep the helper visible after the turn.

### Following a person or animal

Keep the leader ahead on one route, preserve distance changes gradually, and use forward control. Do not alternate between following from behind and static front portraits.

### Handoff

Keep both parties stationary and facing each other. Make the object the dominant change. Show a visible consequence after ownership changes.

### Hazard warning

Establish the hazard or information difference before the warning. Let the warned person visibly stop, yield, retreat, or change route. Do not end on repeated pointing.

### Retrieval

Show why the object is needed, where the retriever goes, one clear retrieval state, return or handoff, and the recipient's next action. Do not make the camera follow a retriever who will naturally return.

### Route and threshold travel

Approach one already-visible threshold, let it enlarge, cross it, then reveal the next space. Preserve source controls when present, but do not add new controls as a substitute for a clear semantic phase. Do not replace the whole environment at a chunk boundary.

### Animals and non-human characters

Prefer simple locomotion, waiting, looking back, carrying one robust object, or leading on one route. Avoid precise paw manipulation, complex mouth-object exchanges, or humanlike multi-step gestures unless central.

---

## Casebook: observed failure → prompt repair

The following cases show how the general observations change actual H3 chunk design. They are not wording templates. Preserve the state transition and first-person geometry, not the nouns.

## Case 1: static establishment consumes the opening

### Failure shape

```text
第一人称POV。明亮诊所入口有玻璃门、灰色地垫、前台、透明伞架、墙面标识、椅子和雨景。最后，我看向地上的雨伞。
```

The intended action is late and weak. H3 may spend the entire chunk holding a polished empty entrance, with no readable cause or participant task.

### Repaired chunk

```text
第一人称POV从玻璃门进入诊所，在灰色地垫内侧停下。我右手收着一把湿的深蓝雨伞，前方偏左的蓝衣前台正在整理预约单；玻璃门右侧的透明伞架随我的进入保持可见。
```

### Why it is better

The entry movement establishes space while introducing ownership, role, route, and the later destination. The environment is learned through goal-relevant action rather than inventory.

## Case 2: a participant appears without an entrance

### Failure shape

Chunk 1 contains only a bench and scarf. Chunk 2 begins:

```text
同一位绿色大衣女人站在前方两米处。
```

She was never introduced, so `同一位` cannot preserve identity. H3 may pop a new person into the composition.

### Repaired boundary

```text
Chunk 1 end: 绿色大衣女人坐在长椅右半边，红围巾穿在她的手提袋把手上。

Chunk 2 start: 绿色大衣女人从同一右侧座位起身，提起手提袋并向右前方车门走出两步；红围巾擦过长椅边缘后滑落。
```

### Why it is better

Identity, start position, object ownership, motion vector, and departure route all persist across the boundary.

## Case 3: first-person turn becomes a hard scene replacement

### Failure shape

```text
Chunk 1 end: 我面对诊所前台。
Chunk 2 start: 玻璃门和雨伞直接出现在正前方。
```

The camera orientation changes without embodied rotation. H3 may render a cut to a different entrance composition.

### Repaired chunk

```text
第一人称POV从前台方向向右后方转动头部和上身。蓝衣前台随视野旋转滑向左侧边缘，灰色地垫从右下方展开，玻璃门连续转入正前方；横放的深蓝雨伞最终位于画面下方中央。
```

### Why it is better

The former subject exits through an image edge while shared floor and lighting anchors bridge the new viewing cone. The destination does not teleport onto the forward axis.

## Case 4: author knowledge is mistaken for visible evidence

### Failure shape

```text
一条属于绿色大衣女人的红围巾放在长椅上。我喊：“女士，您的围巾掉了。”
```

The ownership claim exists only in narration. The first-person wearer has no visible evidence.

### Repaired two-chunk cause

```text
Chunk A: 红围巾清楚穿绕在绿色大衣女人的手提袋把手上。
Chunk B: 她提袋起身时，围巾从同一袋把滑脱并落到长椅；我的视线从她的背影下移到刚落下的围巾。
```

The later warning now follows an event the camera actually observed. If the fall cannot be shown, change the line to a question: `女士，这条围巾是您的吗？`

## Case 5: too many actions compete in one chunk

### Failure shape

```text
我转身走回长椅，弯腰拿起围巾，追上女人，叫住她，把围巾递过去，她接住、围上并登车。
```

This contains a large turn, travel, pickup, pursuit, speech, handoff, use, and threshold crossing. H3 will often render only one endpoint, commonly the woman already holding the scarf.

### Repaired phases

```text
1. Warning: S1 stays by the bench and calls; S2 stops and turns.
2. Confirmation: S2 checks the empty bag handle and confirms ownership.
3. Retrieval/approach: S1 picks up the scarf, walks two steps, and stops within reach.
4. Transfer/use: S2 grips; S1 releases; S2 wraps the scarf.
5. Consequence: S1 yields the route; S2 boards wearing the scarf.
```

### Why it is better

Each chunk has one dominant change in information, position, ownership, or terminal state. Small compatible motions remain grouped.

## Case 6: over-fragmentation destroys one simple operation

### Failure shape from the umbrella-rack story

```text
Chunk 1: fingertips touch the umbrella.
Chunk 2: fingers close around the handle.
Chunk 3: the umbrella rises.
Chunk 4: the body rises.
Chunk 5: the tip aligns over the stand.
Chunk 6: the tip enters the guide ring.
Chunk 7: the tip touches the bottom.
Chunk 8: hands release.
```

For a short non-central placement, these micro-chunks encourage composition resets, object deformation, and long static holds.

### Repaired operation

```text
Chunk A: 我走回地垫，俯身握住自己雨伞的弯柄，将雨伞完整提离门轨；玻璃门开始恢复闭合。
Chunk B: 我直起身体，横移到已可见的门边伞架，把伞尖向下放入插槽；确认伞架承重后松手。
```

### Why it is better

Pickup is one readable phase; placement is another. Fine grip states remain only where support transfer matters.

## Case 7: fragile handoff lacks support transfer

### Failure shape

```text
我把红围巾递给女人。下一段，她已经戴上围巾。
```

The object may teleport, duplicate, or remain in S1's hand because the ownership transition is not visible.

### Repaired handoff

```text
第一人称POV停在女人伸手可及的位置。我右手平稳递出红围巾；她的左手抓住另一端并承担重量。确认她握稳后，我松开右手并收回。她现在单独持有围巾，随即把它绕回颈间。
```

### When to simplify instead

If the story is about reaching a destination rather than the handoff, do not spend several chunks on shared grip. End one chunk with the giver presenting the object and begin the next with the receiver clearly holding it, provided the transfer itself is not the required outcome.

## Case 8: dialogue creates a static portrait

### Failure shape from the pan-fire story

```text
The chef gives a long explanation about oil-fire safety while the flame burns. Everyone stays frozen until the line ends.
```

H3 may hold the chef as a speaking portrait while suppressing urgent action. The behavior is also socially implausible.

### Repaired dialogue/action allocation

```text
Chunk A: the small flare appears; S1 stops stirring and calls, “老师，着火了！”
Chunk B: the classmate starts toward the water; the chef blocks the reach and says, “别拿水！你关火，她拿锅盖。”
Chunk C: S1 turns off the burner while the classmate leaves the water and retrieves the established lid.
```

### Why it is better

Each short line changes information or assigns a task, and the next chunk visibly acts on it. Dialogue does not narrate a procedure that should be performed.

## Case 9: simultaneous multi-person action exceeds the model

### Failure shape

```text
S1 turns off the burner, S2 puts away a knife and speaks, S3 puts on a glove and retrieves a lid, smoke rises, the hood changes speed, and all three step back.
```

Even if physically possible, six competing state changes are unlikely to remain readable in one H3 chunk.

### Repaired division

```text
1. S2 speaks and visibly assigns roles; S1 and S3 only orient toward their targets.
2. S1 places the spoon and turns off the burner; S3 leaves the water untouched and puts on the glove.
3. S3 retrieves and positions the lid while S1 clears the route.
4. S3 slides the lid; the flame disappears; all withdraw.
```

The interaction stays within three people because all roles are necessary, but each chunk limits competing changes.

## Case 10: the ending announces success but does not prove it

### Failure shape

```text
前台说：“谢谢，门口安全了。”
```

The line claims an outcome, but the door, route, and umbrella may still look unchanged.

### Repaired ending

```text
深蓝雨伞直立在门边伞架内。失去阻挡的玻璃门连续闭合，门内灰色地垫完全空出，吹入入口的雨点停止；S1转回前台。
```

### Why it is better

Object support, door state, route clearance, and the participant's next goal are all visible. The story can end without another explanatory line.

## Case 11: full identity repetition resets a person

### Failure shape

Every chunk repeats a long portrait:

```text
一名约三十岁、棕色长发、绿色及膝外套、黑色长裤、棕色鞋、携带棕色手提袋的成年女性通勤者……
```

Repeated re-description can make H3 regenerate rather than continue the person.

### Repaired identity strategy

- First visible introduction: `穿绿色大衣、右手提棕色手提袋的成年女通勤者（S2）`.
- Later chunks: `绿色大衣女通勤者（S2）`.
- Reassert only the anchor needed for current ownership or orientation, such as the tote in her right hand during handoff.

## Case 12: motion strength has no bodily cause

### Failure shape

```text
紧张电影感，镜头剧烈晃动。
```

At a quiet clinic entrance or bus shelter, this can produce unstable motion unrelated to the actor's body.

### Repaired motion evidence

- Clinic routine: restrained head turn, one normal step, stable bend and rise.
- Rainy bus stop: mild walking rhythm and a task-driven downward glance at the fallen scarf.
- Pan fire: a brief backward body recoil when the flame appears, then controlled motion after instruction.

Motion intensity should be caused by walking speed, surface, impact, urgency, lost balance, weather exposure, or a visible hazard—not by genre adjectives alone.

---

## Boundary audit examples

For every adjacent pair, write an internal sentence like these before finalizing:

### Red scarf boundary

```text
At the boundary, S1 is beside the bench facing S2; S2 has stopped two meters ahead and faces back; the scarf remains supported by the bench; the bus door is ahead-right. The next chunk begins without changing any of those states, then S2 checks the empty tote handle.
```

### Umbrella boundary

```text
At the boundary, S1 faces the entrance; the umbrella lies across the lower-center mat and blocks the door; the receptionist remains behind-left. The next chunk begins from this view, then the receptionist points and speaks.
```

### Pan-fire boundary

```text
At the boundary, the burner is off, the spoon is on its rest, S3 holds the lid at the pan's right side, and S1 has stepped back. The next chunk begins with the same support states, then S3 slides the lid from right to left.
```

If this sentence cannot be written without inventing a new position, pose, owner, or view, the chunk boundary is invalid.

## Final per-case H3 audit

- Can the whole event be reconstructed from prompts without hidden prehistory?
- Does each important person enter or become visible through a physical bridge?
- Does each chunk contain one dominant readable change?
- Are small compatible motions grouped rather than atomized?
- Does every turn update the viewing cone and screen direction?
- Is every spoken line caused by visible evidence and followed by a changed action?
- Is every central object introduced before use and continuously supported?
- Does the final chunk prove the physical or social result without explanatory dialogue?

# Jing camera translation controls

Each Ego action has a nonempty `control` list with one string per allocated
repeat. Compilation copies this list unchanged into the final case.

- `"w"`: forward; `"s"`: backward; `"a"`: left; `"d"`: right.
- `"w,a"`: hold W and A simultaneously throughout one slice.
- `""`: no translation keys. Use it for waiting, speaking, hand interaction,
  or an in-place look/turn described in the prompt.
- The list orders slices in time; commas inside a string combine keys within
  that slice. Do not use `*` counts, parenthesized expressions or rotation keys.

Keep one control phase per action. For example, first moving forward and then
left needs two actions, using only `"w"` and only `"a"` respectively. Never encode
that sequence as `"w,a"`. Split a following stop into a stationary action.

```json
["", "", ""]
["w", "w", "w", "w"]
["w,a", "w,a"]
```

The action's timestamp determines its allocated repeat count. For each action,
control length must equal that count. Keep prompts consistent with the current
movement phase and preserve each phase's endpoint for the next action. If an
NPC moves while Ego stays planted, Ego control remains `""`.

A final chunk contains only `prompt`, `repeat` and `control`. Total frames equal
`17 * sum(repeat) + 5`, matching Jing's default first-slice layout. Output
resolution must be divisible by 32. Render at 24 FPS with four denoising steps;
sampler settings belong to the inference configuration, not the cases JSON.

# Complexity budget for stories up to 60 seconds

Complexity is the number of independently readable changes that the audience and video model must track, not word count.

## Complexity units

Count a central additional NPC, independent goal, speaking turn, fragile object operation, route change, knowledge correction, hazard response, extra critical object, or separate terminal proof as one unit. Small supporting motions within one semantic phase do not each count.

## Duration bands

| Duration | Typical actions | Active people including POV | Dialogue turns | Complexity units |
|---|---:|---:|---:|---:|
| up to 15 s | 3–5 | 1–2 | 0–2 | 3–5 |
| >15–24 s | 5–7 | 1–3 | 0–4 | 5–7 |
| 24–30 s | 6–9 | 1–3 | 0–4 | 6–9 |
| >30–50 s | 10–18 | 1–3 | 0–6 | 10–18 |
| >50–60 s | 18–24 | 1–4 | 0–8 | 18–24 |

Action counts are advisory, not hard rejection limits, and necessary control-phase splits may exceed them with a warning. These are defaults, not padding targets: keep a simple story short instead of stretching it to 60 seconds. If a story cannot fit, simplify secondary scenes or another complexity dimension without removing a required physical transition.

## Default hard limits

- More than 0 and no more than 60 seconds. `01:00.0` is a valid endpoint.
- No hard scene-count cap. Every scene or environment transition must be shown as continuous first-person travel through doors, thresholds, corridors, paths, stairs, corners, or other physically legible routes.
- Never use a jump cut, authored cut, teleportation, camera reset, external shot, or unexplained spatial discontinuity. If time is tight, simplify secondary scenes rather than cutting between them.
- At most three active people including POV through 50.0 seconds; above 50.0 seconds, at most four.
- At most four dialogue turns through 30.0 seconds, six through 50.0 seconds, and eight above 50.0 seconds.
- One main goal and at most one causal reversal or correction.
- At most one fragile central interaction.
- No subplot, second unrelated problem, or second terminal outcome.
- At most one speaking role per action.

## Split versus combine

Split competing changes in speaker, ownership, route, facing, or goal. Combine small motions that form one legible phase, such as bending and lifting one nearby object. Do not split a simple task into finger-level micro-actions, and do not combine `turn → walk → retrieve → return → speak → handoff`.

## Simplification order

1. Remove decorative holds, repeated confirmations, and redundant dialogue.
2. Remove an unneeded participant; use an existing role or environment consequence.
3. Remove unnecessary walking or relocate the object within ordinary reach.
4. Reduce simultaneous tasks.
5. Replace a fragile handoff with stable placement when transfer is not central.
6. Keep one causal turn and remove secondary conflict.
7. End at the first durable visual proof.

Never remove the visible cause, decisive response, or terminal result merely to satisfy a number.

## Audit record

```text
target duration:
active people:
main goal:
causal turn:
critical objects:
dialogue turns:
fragile interactions:
route/threshold changes:
planned actions:
terminal proof:
```

# Dialogue guidelines

Use dialogue only when it creates information, choice, correction, refusal, coordination, or consequence that cannot be shown as clearly through action alone.

## Separate turns

Put one speaking role in each dialogue prompt. Split question and answer, offer and refusal, accusation and defense, or clarification and acknowledgment into consecutive prompts.

Keep a dialogue prompt focused on:

`inherited pose and ownership → one speaker's visible delivery → one utterance → listener's small visible response`

Do not add another spoken reply in the same prompt. Avoid combining a long line with walking, a turn, a fragile handoff, and a second reaction. Shorten exposition or add another beat when the line cannot be spoken naturally within the planned 2–5 seconds.

Preserve intended meaning and speaker order. Repair translated, repetitive, or socially unnatural wording, but do not add dialogue that merely narrates visible action.

## Match prompt and dialogue language

- Write a prompt containing Chinese dialogue in Chinese.
- Write a prompt containing English dialogue in English.
- For prompts without speech, use the case's selected language or preserve its established language.
- Begin every Chinese prompt with `第一人称POV` and every English prompt with `First-person POV.`. Do not mix the Chinese token into English prose.
- Do not translate a requested line unless the user asks. Express its language through the surrounding case language, not through a label.

Recommended Chinese form:

```text
第一人称POV延续同一图书馆柜台位置，约45岁的女图书管理员把办好的借阅证放在柜台上，以沉稳清晰的成年女性声线说：“借阅证办好了，请收好。”
```

Recommended English form:

```text
First-person POV. Continuing beside the same station map, the approximately thirty-year-old male attendant points once toward the left corridor and says in a clear adult male voice, "Platform three is on your left."
```

## Disambiguate roles

Maintain a per-case speaker map keyed by unique natural references. Use first-person pronouns for the POV role and stable descriptive references for other speakers. Do not carry a participant's identity from one case into another.

For every recurring speaker, stabilize:

- concrete age or narrow age band;
- gender/presentation unless intentionally neutral;
- social role and relationship;
- one or two visible identity anchors;
- distinct voice age, pitch, cadence, or register;
- spoken language.

Make speakers distinguishable without relying on stereotypes. If two speakers share age or gender, separate them through role, clothing anchors, pitch, cadence, vocabulary, or position. Keep the same voice description throughout the case.

Numbered speaker labels and dialogue wrappers are invalid. Keep one naturally quoted utterance per dialogue prompt, put the speaker identity and vocal description in the surrounding prose, and make the grammatical speaker unambiguous through the stable natural reference.

## Connect speech to causality

Give every line a credible information source and a visible consequence:

- a request motivates retrieval or action;
- a clarification changes the selected object or route;
- a refusal stops a handoff;
- an answer changes the next movement;
- an admission or choice changes the reward or outcome.

Show the cause before the line and the resulting action after it. End the case on the changed physical or social state, not on repeated explanation.

# H3 shot-transition continuity

Apply this guidance when adjacent prompts move the POV, reframe a subject, cross a
threshold, introduce or remove a subject, or otherwise change composition.

Default to one continuous embodied first-person shot.  For every adjacent beat,
record the prior terminal composition, the next opening composition, and the
visible bridge that connects them.  Track camera position and facing, screen
direction, two to four persistent anchors, focal-subject side/distance/scale,
and every story-critical object owner and support.

Use one of these transition modes:

- `continuous_motion`: the same action or camera path progresses monotonically;
- `motivated_reframe`: a visible head/body turn, gaze change, approach,
  deceleration, threshold crossing, or occlusion changes the composition;
- Cuts are not a transition mode in this workflow. Even if the source implies a
  time or location ellipsis, rewrite it as a visible continuous first-person route
  or simplify secondary material until the route fits.

Reject a rewrite boundary when it jumps directly to arrival or completion,
reverses left/right or travel direction without a visible turn, changes subject
scale without approach or retreat, makes a subject or object pop in or out, or
uses an external/reverse shot.  Do not write `画面切到`, `随后来到`, `already
at`, or similar edit language merely to avoid staging the physical bridge.

For doors, arches, and corners, prefer the ordered visual chain:

`approach → frame/edge grows → threshold passes the image edges → adjacent space
appears → embodied turn completes → destination settles in the correct side`

An attractive endpoint does not compensate for a missing transition.  When
duration is tight, remove decorative holds before removing the bridge.

{
  "_pipeline": {
    "schema_version": "6.7",
    "stage": 2,
    "story_decision_sha256": "0000000000000000000000000000000000000000000000000000000000000000"
  },
  "environments": [
    {
      "environment_id": "forest_viewpoint_path",
      "content": "A narrow dirt trail climbs gently through daytime forest, bordered by green shrubs and tall trees. The uphill continuation remains visible behind the guide under soft daylight and light wind."
    }
  ]
}

{
  "_pipeline": {
    "schema_version": "6.7",
    "stage": 2,
    "story_decision_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
    "environment_sha256": "0000000000000000000000000000000000000000000000000000000000000000"
  },
  "render_config": {
    "save_name": "forest_viewpoint_directions.mp4",
    "seed": 10001,
    "height": 544,
    "width": 960,
    "fps": 24,
    "num_inference_steps": 4,
    "control_signal": "camera_delta",
    "discrete_camera": true,
    "prompt_language": "Chinese",
    "visual_style": "自然写实真人电影感，连续具身眼平视角，身份、空间锚点与动作保持稳定",
    "non_diegetic_music": "N/A"
  },
  "intent": {
    "goal": "询问观景台距离并沿向导指示的上坡路线继续前进。",
    "scene_change": false,
    "start_environment_id": "forest_viewpoint_path",
    "end_environment_id": "forest_viewpoint_path"
  },
  "action": {
    "instruction": "接近向导，询问距离，听取回答，然后继续上坡。",
    "supporting_dialogue": [
      "成年男性徒步者以清楚礼貌的成年男性声线问：“前面的观景台还有多远？”",
      "绿色户外夹克的成年女性向导以平静清晰的成年女性声线回答：“再走十分钟就到了。”"
    ]
  },
  "agents": {
    "npcs": [
      {
        "agent_id": "trail_guide",
        "identity": "一名约三十岁、穿绿色户外夹克和深色徒步裤的成年女性向导。",
        "prompt_reference": "绿色户外夹克的成年女性向导",
        "voice": "平静清晰的成年女性声线",
        "interaction_mode": "她在小路旁面对持镜者，通过回答和指向上坡路线提供信息。",
        "state_description": "她最终留在路边，目送持镜者继续前进。"
      }
    ],
    "ego": {
      "agent_id": "ego_hiker",
      "identity": "一名沿林间小路上行的成年男性徒步者和唯一持镜者。",
      "prompt_reference": "成年男性徒步者",
      "voice": "清楚礼貌的成年男性声线",
      "action_list": {
        "total_num": 5,
        "actions": [
          {
            "action_id": 1,
            "timestamp": "00:00.0-00:03.0",
            "action_type": "navigation",
            "action_plan": "沿上坡土路接近向导，在两步距离减速并停稳。",
            "speaker_agent_id": null,
            "dialogue_refs": [],
            "scene_dynamics": [
              {
                "environment_id": "forest_viewpoint_path",
                "description": "在 forest_viewpoint_path 中，土路和灌木因我前进而向画面下方滑过，向导随距离缩短连续放大；柔和日光保持稳定。"
              }
            ],
            "action_description": "第一人称POV我保持成年男性徒步者的自然眼高，沿缓慢上升的土路走向绿色户外夹克的成年女性向导。两侧灌木随脚步后移，我在她面前两步处减速并完整停稳，上坡路线仍在她身后可见。",
            "overall_soundscape": "自然脚步、轻微衣料声、林间风和远处鸟声保持空间层次。",
            "control": ["w", "w", "w", "w"]
          },
          {
            "action_id": 2,
            "timestamp": "00:03.0-00:05.5",
            "action_type": "manipulation",
            "action_plan": "保持停步，向向导询问观景台距离。",
            "speaker_agent_id": "ego_hiker",
            "dialogue_refs": [
              "成年男性徒步者以清楚礼貌的成年男性声线问：“前面的观景台还有多远？”"
            ],
            "scene_dynamics": [
              {
                "environment_id": "forest_viewpoint_path",
                "description": "在 forest_viewpoint_path 中，相机位置不变，向导、土路和灌木保持原有尺度；向导真实转向我倾听。"
              }
            ],
            "action_description": "第一人称POV我停在同一位置，面对两步外绿色户外夹克的成年女性向导，以清楚礼貌的成年男性声线问：“前面的观景台还有多远？”她保持安静并看向我，完整听完问题。",
            "overall_soundscape": "我的近场成年男性问话位于林间风、树叶摩擦和远处鸟声之前。",
            "control": ["", "", "", ""]
          },
          {
            "action_id": 3,
            "timestamp": "00:05.5-00:08.0",
            "action_type": "manipulation",
            "action_plan": "留在原地听向导回答并观察她指向上坡路线。",
            "speaker_agent_id": "trail_guide",
            "dialogue_refs": [
              "绿色户外夹克的成年女性向导以平静清晰的成年女性声线回答：“再走十分钟就到了。”"
            ],
            "scene_dynamics": [
              {
                "environment_id": "forest_viewpoint_path",
                "description": "在 forest_viewpoint_path 中，固定植被和路面保持稳定；向导真实抬手指向她身后连续可见的上坡土路。"
              }
            ],
            "action_description": "第一人称POV我继续停在原地。绿色户外夹克的成年女性向导以平静清晰的成年女性声线回答：“再走十分钟就到了。”她随后抬手指向身后继续上升的土路，我保持安静并看清方向。",
            "overall_soundscape": "向导的近场成年女性回答清晰可辨，衣袖轻响，林间风和鸟声持续。",
            "control": ["", "", ""]
          },
          {
            "action_id": 4,
            "timestamp": "00:08.0-00:08.7",
            "action_type": "navigation",
            "action_plan": "停在原位向左转动视角，让上坡路线居中。",
            "speaker_agent_id": null,
            "dialogue_refs": [],
            "scene_dynamics": [
              {
                "environment_id": "forest_viewpoint_path",
                "description": "在 forest_viewpoint_path 中，我原地向左转动视角，固定植被和上坡路线连续滑过画面，路线在结束时居中。"
              }
            ],
            "action_description": "第一人称POV我承接向导指向上坡土路的状态，停在原位向左转动视角，让上坡路线进入画面中央；这一阶段只转向，不向前行走。",
            "overall_soundscape": "转身时衣料轻响，林间风和鸟声持续。",
            "control": [""]
          },
          {
            "action_id": 5,
            "timestamp": "00:08.7-00:10.0",
            "action_type": "navigation",
            "action_plan": "沿已经居中的上坡路线向前，从向导身侧经过。",
            "speaker_agent_id": null,
            "dialogue_refs": [],
            "scene_dynamics": [
              {
                "environment_id": "forest_viewpoint_path",
                "description": "在 forest_viewpoint_path 中，上坡路线保持居中，近处土路和植被随我前进连续后移。"
              }
            ],
            "action_description": "第一人称POV我承接原地转向后的终点，沿正前方的上坡土路向前行走，从绿色户外夹克的成年女性向导身侧以自然距离经过；我保持朝向，不再转动视角。",
            "overall_soundscape": "自然脚步重新开始，林间风和鸟声保持连续。",
            "control": ["w", "w"]
          }
        ]
      }
    }
  }
}

## minimal continuous-shot seam rules

This appendix has final precedence only for continuity between adjacent actions. It does not change the schema, Story Decision semantics, role or dialogue bindings, object-support requirements, repeat allocation, or uniform-control validation.

- Preserve the Story Decision's events, order, and action ownership. Do not add, delete, reorder, or further split a semantic event merely to improve continuity. Keep the action count as low as the semantic requirements and control validator allow, and do not add a stationary hold beyond one already required by those constraints.
- Keep every pair of adjacent actions in the same continuous first-person take. Authored cuts, time-skip cuts, reverse shots, external shots, teleportation, and scene or camera resets are always forbidden; show a physically continuous route or simplify secondary material.
- For every action after the first, begin `action_description` with one concise clause that inherits the exact prior endpoint: the same environment, camera position, height and facing; the focal participant's side, distance and scale; two stable landmarks; lighting; and any task-relevant hand or object support. Reuse the exact `prompt_reference` and introduce no new prop, pose, or event in this seam clause.
- When either adjacent action contains camera motion, describe the visible spatial bridge across the boundary: fixed anchors slide, grow, recede, or cross the frame consistently; subject scale changes only through shown motion; and the previous endpoint is the next opening composition. Do not begin at an unexplained arrival or allow a jump cut, teleportation, direction reversal, or scene reconstruction.

## mandatory dialogue-copy gate — 台词未原样写入动作描述即不合格

**Acceptance is all-or-nothing: one missing referenced utterance, or any omitted part of it, makes the ENTIRE sample FAIL. This is a mandatory rejection condition, never a warning or an advisory quality issue. Repair every omission before emitting the response; otherwise the sample is not qualified.**

`dialogue_refs` declares the line to speak; the corresponding `action_description` must actually contain that line. Keeping the line only in root `action.supporting_dialogue`, `dialogue_refs`, `action_plan`, `overall_soundscape`, or a different action does NOT satisfy this requirement. Do not assume Compilation will insert a missing line.

For EACH action with a nonempty `dialogue_refs`:

1. Copy the complete selected root `action.supporting_dialogue` string exactly into `dialogue_refs`, as already required. Then extract its quoted utterance and copy that utterance verbatim into this action's `action_description`, with Chinese `“...”` or English straight double quotes. The surrounding narration may be adapted to first-person POV, but the quoted text must remain unchanged, including language, words, punctuation, and symbols. In JSON, escape English double quotes as `\"`; after JSON decoding they must be ordinary double quotes in the description.
2. Explicitly attribute the line to the declared `speaker_agent_id` with the consistent speaker identity and voice. Preserve one speaker turn per action and the required first-person opening. Do not add another speaker's answer to the same action.
3. “问出问题”, “说了那句话”, “回答了我的问题”, “ask my question”, “respond to me”, a translation, or a paraphrase WITHOUT the verbatim quoted utterance is INVALID / 不合格, even when it conveys the same intent. Such output triggers `referenced utterance is absent from action_description` and, when no quoted speech remains, `dialogue action_description lacks quoted speech`.
4. Never evade this gate by deleting or emptying a required `dialogue_refs`, removing the root line, dropping the speaking event, or moving it to another action. Repair this action's description by restoring the original quoted line.

Chinese example — partial fields of the SAME action:

```json
{
  "dialogue_refs": ["第一人称购物者以礼貌清晰的成年声线问：“请问这张优惠券是在右拐的这家店使用吗？”"],
  "action_description": "第一人称POV我停在店员面前，右手握着红色纸质优惠券，以礼貌清晰的成年声线问：“请问这张优惠券是在右拐的这家店使用吗？”店员保持安静，听完我的问题。"
}
```

INVALID counterpart: `第一人称POV我停在店员面前，以礼貌清晰的成年声线问出问题。` It omits the quoted line, even though `dialogue_refs` still contains it.

English example — partial fields of the SAME action:

```json
{
  "dialogue_refs": ["The first-person shopper asks in a clear polite adult voice: \"Where is the entrance?\""],
  "action_description": "First-person POV. I remain stopped in front of the clerk and ask in a clear polite adult voice: \"Where is the entrance?\" The clerk stays silent and listens."
}
```

INVALID counterpart: `First-person POV. I remain stopped in front of the clerk and ask my question about the entrance.` The intended meaning does not replace the missing literal utterance.

If an already quoted reference is a vocalization such as `"*soft meow*"`, preserve the exact quoted `*soft meow*` in the corresponding description; `responds with a soft meow` alone does not pass the literal-copy check. This does not authorize inventing dialogue or converting ordinary ambient sounds into speaking turns.

Final silent self-check: after composing the entire envelope, iterate through ALL actions, extract every quoted utterance from each `dialogue_refs` entry, and verify that the exact utterance occurs inside quotation marks in that SAME action's decoded `action_description`. Check every action, not just the examples or the first speaking action. If any line is absent, shortened, translated, paraphrased, or unquoted, the envelope is NOT QUALIFIED / 不合格: repair it before returning the JSON. Return only the required JSON envelope, without this checklist or validation commentary.

## mixed-control split rule

This rule takes precedence over any earlier example that mixes control entries within one action or relies on Compilation to split it.

- **同一个 action 的 `control` 条目必须完全一致；混合轨迹即不合格。** If the camera retreats, then moves right, then stops, split these sequential phases into separate actions BEFORE returning JSON. Never replace mixed entries with one control or combine them with commas to disguise sequential motion as simultaneous.
- Example: `["s", "s", "d", "d", "", ""]` must become a backward action using only `s`, a rightward-translation action using only `d`, and a stationary action using only `""`. The stationary phase may merge into the next action only if it is also stationary and preserves event order and the one-speaking-turn limit. If the story additionally requires turning, retain a separate appropriate yaw phase; `d` is translation, not a turn.
- Each new action describes ONLY its own motion phase and inherits the previous endpoint. Preserve the original events and all quoted dialogue; do not duplicate or omit a line during splitting. Actions without dialogue use `dialogue_refs: []` and `speaker_agent_id: null`.
- After splitting, renumber all `action_id` values as consecutive JSON integers, update `total_num`, give every action continuous positive-duration timestamps, and recompute ALL control lengths using the existing case-wide repeat allocation. Preserve the total duration. Necessary control-phase splits take priority over advisory action-count targets.
- Final self-check: every schedule is nonempty and satisfies `len(set(control)) == 1`, its description executes only that phase, and IDs, timestamps, repeat lengths, and dialogue bindings are valid. Repair failures before output; do not expect normalization or Compilation to split actions.

## explicit NPC-gesture actor and no-POV-hand gate

This appendix has final precedence whenever an NPC performs a pointing or directional hand gesture. It strengthens actor binding and first-person framing without changing the schema, dialogue, control, or action-splitting requirements.

- In every `action_description` sentence that describes or continues an NPC gesture, name that NPC's exact `prompt_reference` as the grammatical subject. A bare pronoun such as `he`, `she`, `they`, `他`, `她`, or `他们` is insufficient because it does not identify whose hand is moving. `action_description` must still contain no S marker; the exact `prompt_reference` provides the stable visible identity.
- State that this named NPC is the only person gesturing. Explicitly state in the same action that the first-person camera wearer does not point, reach, copy, follow, or mirror the gesture.
- Keep the NPC's visible hand and arm anatomically connected through wrist, sleeve, elbow, and shoulder to the named NPC. A detached hand, wrist, forearm, or sleeve entering from any image edge is invalid, even if the prose intended it to belong to the NPC.
- For the full duration of the NPC-gesture action, including any stationary viewing or direction-confirmation beat, every POV hand, wrist, forearm, and sleeve must remain completely outside the frame. Do not describe a POV hand as lowered, still, or holding something if any part of it would remain visible. Never add a POV hand to acknowledge the NPC gesture.
- Reject and rewrite the action if any visible hand could be interpreted as the POV camera wearer's hand, if the gesturing actor is identified only by a pronoun, or if the arm-to-body connection is not explicit in the prompt.

Use a prompt shape like this, adapted to the actual NPC and target geometry:

```text
The green-jacketed adult woman guide is the only person gesturing. The green-jacketed adult woman guide raises one sleeve-connected arm from her visible shoulder and points toward the already-visible cafe entrance; her fingertip aligns with that entrance. The first-person camera wearer does not point, reach, follow, or mirror the gesture. All POV hands, wrists, forearms, and sleeves remain completely outside the frame throughout this action.
```

INVALID: `She points toward the cafe while I look in that direction.` This leaves the gesture actor underspecified and does not exclude a POV hand.

Final silent self-check: for every NPC gesture, verify that the exact NPC `prompt_reference` names the gesture actor, only that NPC gestures, the arm is visibly connected to that NPC's body, and no POV hand, wrist, forearm, or sleeve can appear. Any failure makes the sample NOT QUALIFIED; repair it before returning JSON.

## One-minute continuous-take policy — final precedence

This section has final precedence over every earlier duration or transition example.

- Accept only `0 < total duration <= 60 seconds`; `01:00.0` is a valid final timestamp. Preserve shorter stories at their natural length and never pad merely to approach one minute.
- Keep the existing bands through 30 seconds. For `>30–50` seconds, use 10–18 actions as an advisory target, no more than 3 active people including POV, and no more than 6 dialogue turns. For `>50–60` seconds, use 18–24 actions as an advisory target, no more than 4 active people including POV, and no more than 8 dialogue turns. Exactly `50.0` seconds remains in the first band. People, dialogue, and duration limits are hard failures; action targets are warnings only. Necessary uniform-control phase splits may exceed the advisory action target.
- There is no fixed scene-count limit. However, every scene or environment change must occur through visible continuous first-person physical movement. Show the full spatial bridge through doors, thresholds, corridors, paths, stairs, corners, or other physically coherent routes, preserving position, facing, anchors, subject scale, object support, and screen direction.
- Jump cuts, hard cuts, authored cuts, time-skip cuts, teleportation, camera resets, scene resets, external shots, reverse shots, and unexplained arrivals are always invalid, even when requested by the source. If all secondary scenes cannot fit with their physical routes, simplify or remove secondary scenes; never replace the route with a cut.
- Before returning JSON, verify that every adjacent action inherits the prior physical endpoint and that no `action_description` or `scene_dynamics.description` uses unnegated cut, teleport, or reset language.

## Explicit reference-image grounding — final precedence

Story Decision may contain a top-level `ref` array. Its nth element describes `<Picture n>` (1-based input order). Story generation has already inspected the images; do not re-caption them or request raw images. Captions help identify the intended subject, scene, or object; the final descriptions must keep the actual image references instead of replacing them with caption-derived appearance prose.

- In every relevant `action_description`, explicitly name the image-grounded subject or setting using its exact `<Picture N>` label, e.g. "the young man in <Picture 2>" or "the square shown in <Picture 1>". Keep the Story generation role's stable prompt_reference for actor binding. Write the action, motion, spatial relations, dialogue, and changes explicitly; the image supplies appearance, not an implied action.
- Example: "First-person POV. I approach the young man in <Picture 2> at the entrance of the shop shown in <Picture 1>. The young man in <Picture 2> turns toward me." Do not replace these references with an exhaustive clothing or architectural caption. Brief distinguishing details are allowed when an image contains several subjects.
- Each action is conditioned separately: repeat the relevant image references in each action where their subject or setting is used. Keep the same numbering throughout the case, including when an action uses only a subset of images. Never renumber that subset, invent an unavailable index, or treat `<Picture N>` as an internal S/O/B entity marker.
- Keep scene and character references separate when they come from different images. A reference used as the subject of a photograph must be described as such, not introduced as a physically present actor. Do not force unrelated reference images into actions.
- Preserve the exact ASCII spelling, brackets, capitalization, and integer in `<Picture N>` in both Chinese and English prompts. Do not emit `<|vision_start|>`, `<|image_pad|>`, `<|vision_end|>`, or a standalone visual-token prefix: the downstream encoder supplies those automatically.
- If `ref` is absent or `[]`, keep text-only behavior and emit no picture references. Retain the two-key response envelope, the existing schema, and all other action/dialogue/continuity rules. Before output, check that every reference index exists and that image-grounded actions retain their explicit references.

### Mandatory per-action grounding check

Treat EACH `action_description` as a standalone description for image grounding. Earlier actions, `ref` captions, role declarations, and Environment content do not substitute for an explicit reference in the current action. This does not reset narrative continuity.

1. Carry Story generation's explicit scene/image bindings into Environment `content`. For the current action, identify the bound scene or scene part actually used by its `scene_dynamics` and camera view, and the reference-grounded people or objects that are visible. Do not infer a character reference from a scene-only image.
2. Write the applicable exact `<Picture N>` labels INTO the corresponding scene, actor, or object noun phrases in `action_description`. If the camera remains in a referenced shop, repeat "inside the shop shown in <Picture 2>" in EVERY action there, including silent pauses, dialogue, and close-ups. "the same shop", "still there", or "as before" alone is insufficient. Keep the exact role `prompt_reference` when naming an actor.
3. Images supply appearance and identity. Explicitly describe the current motion, camera framing, position, interaction, and spoken words. Do not copy a long caption or append an unbound instruction such as "use the reference images". For multiple views of a scene, use the established reference for the visible part; do not list all images indiscriminately. Do not cite an absent actor or an unrelated scene just to increase reference coverage.
4. Before returning JSON, inspect EVERY action, including all middle actions. If it uses an image-bound scene, actor, or object but its description omits that binding, rewrite that action before output. An opening or closing action with the label does not make the middle actions pass. Also verify that every used image index exists. If there are no reference images, skip image grounding and keep descriptions free of picture labels.

Example with a scene-only reference: Story generation binds the shop interior to `<Picture 2>`; no character image is provided.
- Correct action 1: "First-person POV inside the shop shown in <Picture 2>. I walk toward the counter."
- Correct action 2: "First-person POV at the counter inside the shop shown in <Picture 2>. I stop and look down at the empty countertop."
- Incorrect action 2: "I remain in the same shop and look down at the countertop." The current description has lost the scene's image reference.
- Also incorrect: "The shopkeeper in <Picture 2> turns toward me." A scene-only reference does not establish a shopkeeper's identity.

## Case analysis: turn a Story Decision into executable action phases

This appendix uses a western-town photo inquiry to explain failures observed in a 41.292-second rendered case. The source Story Decision had 10 beats totaling 41 seconds. Its Action generation output also had 10 actions, but matching those counts did not mean the physical phases were implemented correctly. These examples are proposed refinements, not verified video fixes. Keep the supplied Story Decision's meaning, dialogue and timing budget; no new JSON fields are required.

### What went wrong and where

| Evidence from this case | Interpretation and Action generation response |
|---|---|
| Opening prose said approach, decelerate, stop, park luggage and release the handle; every control entry was `w`. | The prose includes a stationary endpoint but control never settles. Split approach from stationary parking/settling, preserving the same doorway and distance at the boundary. |
| Final prose said turn right, then follow forward; all ten entries were `w`. | Separate the in-place turn (`""`, rotation described in prose) from forward following (`w`). Do not command forward movement during an in-place turn. |
| Around 26–30 seconds, the returned photo occupied the foreground and cropped the face. One action contained return, receive, lower and spoken response. | The instruction to lower was present, so this is not a missing-instruction diagnosis. Separate the completed handoff/lowering state from the face-focused response when they compete for attention. |
| Luggage appeared near the young man although text placed it at POV's right foot. | Translate body-relative placement into scene depth: luggage beside the camera wearer in the near foreground, young man farther ahead. Preserve ownership after the object moves out of frame. |
| Retrieval included unfolding a photo. | This operation was already in the supplied Story Decision, not invented by Action generation. Do not silently remove source operations here; resolve that content upstream. Do not introduce additional operations yourself. |

### Example A: approach, then stop

Incorrect: one prompt narrates walking, stopping and parking luggage while its entire control array is `w`.

Use separate actions within the original approach/settle interval:
- Moving action: approach the established doorway with `w` throughout; end at the conversational location without describing the later parking action.
- Stationary action: use `""` throughout. Begin at that same location, scale and view; park luggage beside POV and release the handle. Keep the young man ahead and the luggage nearer to POV. Do not replay the approach or add a zoom.

Allocate time/repeats between the two phases using the existing compiler rules. Do not duplicate the original full duration into both actions.

### Example B: photo return, then attention to the speaker

Separate the physical transition from the subsequent sustained state:
- Handoff/lowering action: the young man offers the photo, POV grasps it before he releases, then lowers it below the main view. End with the photo supported by POV and both people no longer exchanging it.
- Response action: inherit that completed state. The young man's face is the focus, his hands have withdrawn, and the photo remains low; deliver the privacy line once. Do not describe receiving or displaying the photo again.

Each action still carries applicable reference bindings. An out-of-frame photo need not be visually displayed just to repeat its image label. If the plan explicitly includes looking down and back up, give those camera rotations their own uniform control phases; otherwise do not invent a head movement. Merely lowering a hand does not itself require tilting the camera.

Preserve the total interval and allow enough time for the actual line. Do not shorten speech to make room for an unnecessary pose. If the interval cannot support the required events naturally, report the source timing conflict rather than silently speeding up or changing the Story Decision.

### Example C: take luggage, turn, then follow

For this case's final 7-second interval, distinguish:
1. Stationary grasp of the already parked luggage handle: `""`.
2. Turn toward the established alley: use `""` and describe the rightward turn in prose, without forward motion.
3. Follow the young man along the visible route: `w`, without continuing the turn.

These are phase examples, not fixed repeat counts or mandatory directions for every scene. Allocate their timestamps and repeat counts within the supplied interval. Keep the young man ahead, the photo low and luggage ownership continuous. Describe each action's current movement only, inheriting the preceding endpoint.

If the intended action actually requires turning while advancing, use `w` for translation and describe the turning path in prose. Keep turn-then-walk phases separate.

### Before returning actions

A Story generation beat can expand into multiple Action generation actions. At every split, preserve chronological timestamps, dialogue order, ownership, reference bindings and the preceding end pose; derive control lengths from the allocated duration. Within each action keep one uniform control phase. Check that prose and controls describe the same phase, and that each utterance is delivered once rather than copied into every split action. Apply these distinctions to new cases without copying the photo, luggage, setting or numerical durations.
