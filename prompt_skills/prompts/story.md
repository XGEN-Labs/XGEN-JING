# Jing Story Planning

## Input and output

Plan a first-person video story from the supplied request and reference images. Return only the story JSON described below.

The user message supplies the raw narrative, source H3 or case evidence, and explicit constraints. Produce exactly one complete Story Decision JSON object and no prose wrapper. This API transport rule takes precedence over any retained saved-path reporting or stop/report mechanics.

This execution permits one OpenAI API call. After the response, the caller saves and validates the JSON. A validation failure terminates this execution; do not assume an automatic repair call.

## Story plan

Create exactly one `<base>_story.json`. This is the only stage allowed to read the raw narrative, source H3, and explicit user or project constraints.

## Produce the decision

Treat the source as evidence of intended events, not an untouchable screenplay. Separate hard facts from repairable staging, then resolve causal order, role responsibility, information access, motivation, object support and ownership, spatial feasibility, interaction complexity, dialogue purpose, duration, render policy, and visible terminal proof.

Use the embedded Story Decision JSON template below as the structural starting point. Preserve the Story generation pipeline marker. Record deliberate repairs and discarded details explicitly rather than silently changing them.

Stop after Story generation. The next stage receives only the persisted Story Decision; raw input and unstored reasoning must not cross the boundary.

## Story schema

Story Decision is the only bridge from raw input to Action generation. It must be complete enough that Action generation never needs to reopen the source.

## Required shape

```json
{
  "_pipeline": {"schema_version": "6.7", "stage": 1},
  "base_name": "filesystem_safe_case_name",
  "ref": [],
  "source_assessment": {
    "intended_event": "<string>",
    "hard_facts": ["<string>"],
    "repairs": ["<problem -> decision>"],
    "discarded_details": ["<string>"]
  },
  "story_contract": {
    "pov_role_id": "ego_role",
    "immediate_goal": "<string>",
    "visible_trigger": "<string>",
    "interaction_reason": "<string>",
    "decisive_response": "<string>",
    "visible_result": "<string>",
    "next_state": "<string>"
  },
  "roles": [
    {
      "role_id": "ego_role",
      "is_camera_wearer": true,
      "identity": "<string>",
      "prompt_reference": "<stable natural reference>",
      "goal": "<string>",
      "known_information": ["<string>"],
      "capability_and_authority": "<string>",
      "possessions": ["<string>"],
      "relationship": "<string>",
      "likely_next_action": "<string>"
    }
  ],
  "objects": [
    {
      "object_id": "plain_identifier",
      "initial_owner": "<role_id or none>",
      "support_chain": ["beat 1: support -> beat 2: support"],
      "terminal_owner_or_support": "<string>"
    }
  ],
  "information_evidence": [
    {
      "role_id": "<role_id>",
      "fact": "<string>",
      "source": "sight | sound | dialogue | prior-role-knowledge | physical-evidence",
      "learned_at_beat": 1,
      "resulting_action": "<string>"
    }
  ],
  "environment_requirements": [
    {
      "environment_id": "<string>",
      "content": "<complete static description>"
    }
  ],
  "spatial_plan": {
    "camera_start": "<string>",
    "stable_anchors": ["<string>"],
    "route": ["<string>"],
    "terminal_composition": "<string>"
  },
  "dialogue": [
    {
      "speaker_role_id": "<role_id>",
      "language": "Chinese | English",
      "utterance": "<exact words without quotation marks>",
      "purpose": "<information/action change>"
    }
  ],
  "beats": [
    {
      "beat_id": 1,
      "duration_seconds": 3.0,
      "action_type": "navigation | manipulation",
      "dominant_change": "<string>",
      "participants": ["<role_id>"],
      "environment_ids": ["<environment_id>"],
      "plan": "<first-person feasible action plan>",
      "end_state": "<camera, participant, object, and information state>"
    }
  ],
  "render_policy": {
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
  }
}
```

## Invariants

- Exactly one role is the camera wearer and matches `story_contract.pov_role_id`.
- Role IDs, object IDs, environment IDs, and beat IDs are unique.
- Beats are sequential, positive-duration, and total no more than 60 seconds.
- Scene count has no fixed cap, but every environment change must be reached through visible, continuous first-person physical movement. Jump cuts, authored cuts, teleportation, camera resets, and unexplained spatial discontinuities are forbidden.
- Every beat references declared roles and environments.
- Every dialogue speaker is declared; each line has a causal purpose.
- Every important ownership claim has visible, audible, role-based, or physical evidence.
- Object support chains begin before use and end in the stated terminal support.
- The last beat's end state visibly proves `story_contract.visible_result` and `next_state`.
- Render at 24 FPS with four denoising steps. Height and width must be positive multiples of 32. Render policy contains every value Compilation needs. Jing controls translation with WASD and view rotation with IJKL: i/k look up/down, j/l turn left/right. Keep action prose and control keys consistent; in-place turns use rotation keys without translation keys.
- Render policy uses `control_signal: "camera_delta"` and `discrete_camera: true`; Action generation will convert the spatial plan into a required per-repeat discrete control schedule.

Do not include final H3 prompts, S markers, `<d>` wrappers, chunks, or repeats in Story Decision. Those belong downstream.

# Script generation logic: principles grounded in concrete cases

This reference turns the original question-and-answer comparisons into principles for first-person stories up to 60 seconds. Do not memorize the conclusions alone: understand why the correct answer fits the role, time, and question better than the distractors, then apply that relationship to new stories.

## 1. How to use the cases

Analyze each case in the same order:

```text
Original context and question
→ The logical constraint satisfied by the correct answer
→ The dimension substituted by the incorrect answer
→ The resulting problem in a script
→ A repair through visible action within 60 seconds
```

Do not copy character names or surface actions. Extract the structure of roles, information, time, causality, and state changes.

---

## 2. Dimension one: match the semantic function

### QA case: `train-17` / `xWant`

> **Context:** Ash rode hard and put away his wet clothes to let them dry for a few hours.
> **Question:** What will Ash want to do next?
> **Dataset-labeled answer:** `lazy`

Reject this noisy case. The question asks for a next action, but `lazy` is a trait or state, not an executable action.

### Script error

```text
After the fire is extinguished, the trainee next feels guilty.
```

Guilt is an emotional reaction, not a next action; a video cannot render it directly as an action.

### Plausible rewrite

```text
After the lid smothers the fire, the trainee looks down at the knob she turned up, admits her mistake, and places a lid beside the next cold pan before starting.
```

The sequence makes an internal reaction visible, expresses it in speech, and shows a next action informed by learning.

### Principle

Label each action phase with its main function: `MOTIVE / PRECONDITION / ACTION / EFFECT / EMOTION / NEXT_ACTION`. If a description cannot realize that function, rewrite it instead of filling it with adjectives.

---

## 3. Dimension two: assign actions to the correct roles

### QA case: `train-54` / `oWant`

> **Context:** Taylor saved other people's teeth from decay by providing good toothpaste.
> **Question:** What will Others want to do next?
> **Correct:** `thank Taylor`
> **Incorrect:** `teach them how to floss`; `teach them how to use mouthwash`

The correct answer is the beneficiaries' social response. The incorrect answers transfer the helper's teaching responsibility to the people receiving help, reversing the roles.

### Script error

A receptionist asks a random visitor to put away an unidentified umbrella without establishing its owner or the visitor's responsibility. The visitor immediately obeys as a mere plot device.

### Plausible rewrite

First show S1 laying their own wet umbrella across the entrance mat. It prevents the glass door from closing. The receptionist says, "Sir, your umbrella is blocking the door." S1 puts away their umbrella. Ownership, responsibility, and the acting role agree.

### Principle

For every event, identify the initiator, target, owner, beneficiary, harmed party, informed party, and responsible party. Proximity to an object does not automatically make a character responsible for it.

---

## 4. Dimension three: preserve temporal order

### QA case: `train-2` / `xWant`

> **Context:** Remy was on the water and had baited the hook.
> **Question:** What will Remy want to do next?
> **Correct:** `cast the line`
> **Incorrect:** `put the boat in the water`; `invite Kai out on the boat`

The incorrect answers are not always wrong; they are too late at this point in time.

### Script error

A character has already reached the bus door before the next segment first shows the bus arriving, or the scarf has already been returned before its fall is shown.

### Plausible rewrite

```text
The bus approaches and opens its door
→ The woman passenger rises hurriedly
→ The scarf slips off her bag handle
→ S1 sees it and calls out
→ The woman stops to check
```

### Principle

The presentation may omit decoration, but never the trigger that makes a later reaction possible. Place every action correctly within `BEFORE / DURING / AFTER / NEXT`.

---

## 5. Dimension four: do not reverse cause and effect

### QA case: `train-76` / `xEffect`

> **Context:** Taylor received the winning lottery ticket and won the jackpot.
> **Question:** What will happen to Taylor?
> **Correct:** `Have more money than before`
> **Incorrect:** `Buy more lottery tickets next time`

Increased wealth is the direct result that has already occurred; buying more tickets is only a possible later action.

### Script error

```text
The receptionist says, "The entrance is safe now," so S1 puts the umbrella in the stand.
```

The actual causal order is that S1 removes the umbrella, the door closes normally, and the entrance becomes safe.

### Plausible rewrite

```text
The umbrella blocks the glass door
→ The receptionist points out the problem
→ S1 removes the umbrella
→ The glass door closes completely
→ Rain no longer blows into the entrance
```

### Principle

Test every connection with "Because A, therefore B." Dialogue may identify a cause but cannot replace the physical action that produces a result.

---

## 6. Dimension five: motivation must explain the action

### QA case: `train-15` / `xIntent`

> **Context:** Austin saw a purse on top of a moving car and ran alongside to get the driver's attention.
> **Question:** Why did Austin do this?
> **Correct:** `help another person`
> **Incorrect:** `be nice`; `practice for a marathon`

`practice for a marathon` explains running but not the purse, car, or warning to the driver; `be nice` is too broad.

### Script error

A random visitor spends several actions handling an unfamiliar object after one request from a receptionist. Alternatively, a stranger takes a major risk to help someone without time pressure, responsibility, or an established relationship.

### Plausible rewrite

Establish that the object belongs to S1, or let S1 see it fall from the other person's hand. Low-cost help needs only an immediately visible problem; high-cost help also needs a stronger relationship, responsibility, or risk-related reason.

### Principle

Motivation must explain why this target, why now, why this method, and why the character accepts the cost.

---

## 7. Dimension six: establish action prerequisites

### QA case: `train-26` / `xNeed`

> **Context:** Aubrey understood the teacher's question and answered.
> **Question:** What did Aubrey need beforehand?
> **Correct:** `know the information`
> **Incorrect:** `ask for a gold star`; `skip her class`

Correctly answering a knowledge question requires prior knowledge. Requesting a reward comes afterward; skipping class undermines the prerequisite.

### Script error

A classmate suddenly knows how to handle a pan fire or acquires a lid without explanation, or S1 walks directly to an umbrella stand they have never seen.

### Plausible rewrite

- Establish the lid and heat-resistant gloves on a fixed rack in the first segment.
- Let the chef, as the professional, give brief task assignments.
- Bring the destination into peripheral view before a character moves toward it.

### Principle

Before a critical action, check knowledge, ability, tools, authority, and reach. The more directly an ability or prop solves the central problem, the earlier it should be established.

---

## 8. Dimension seven: characters must have access to information

### QA case: the original red-scarf script

The original script first shows a red scarf on a bench but immediately declares in narration that it belongs to the woman in green. S1 has seen no evidence of ownership yet says, "You left your red scarf on the bench."

This is author knowledge, not information available from the scene.

### Plausible rewrite

First show the red scarf looped through the woman's handbag handle. After the bus arrives, the scarf slips from the handle onto the bench within S1's view. S1 then has a reliable source for calling, "You dropped your scarf."

If the fall cannot be shown, ask instead:

> "Ma'am, is this red scarf yours?"

### Principle

For each judgment, record what the character needs to know, whether the source is sight, sound, dialogue, or prior role knowledge, when they learn it, and what action follows. Characters cannot possess hidden facts available only to the director.

---

## 9. Dimension eight: emotion must fit the goal and timing

### QA case: `train-22` / `xReact`

> **Context:** Quinn finally found a puppy missing for a week.
> **Question:** How would Quinn feel?
> **Correct:** `very relieved`
> **Incorrect:** `excited`; `very excited`

Excitement and relief are both positive, but recovering something lost primarily resolves an ongoing risk.

### Script error

A character mechanically says "Thank you" after finding a lost item, or remains in exactly the same frightened pose after danger has passed.

### Plausible rewrite

The woman passenger first checks the empty bag handle and her neck, realizing that the scarf is missing. After receiving it securely and wrapping it around her neck, she relaxes her shoulders, nods to S1, and continues boarding. The emotional change follows confirmation and resolution rather than appearing in advance.

### Principle

Emotion comes from a character's interpretation of who changed which goal and how. Express it through posture, action rhythm, distance, and the next choice rather than an emotion label alone.

---

## 10. Dimension nine: the next action must be concrete and continuous

### QA case: `train-8` / `xWant`

> **Context:** Quinn wanted to help clean a messy room.
> **Question:** What will Quinn want to do next?
> **Correct:** `Pick up the dirty clothes`
> **Incorrect:** `help out a friend`

`help out a friend` merely repeats the overall goal; picking up dirty clothes is an executable next step.

### Script error

```text
S1 realizes the entrance is unsafe and starts addressing the problem.
```

### Plausible rewrite

```text
S1 pockets the phone, turns and walks back to the mat, bends to grip the curved handle of their own umbrella, and lifts it completely clear of the door track.
```

### Principle

Test an action description with "Who uses what to do exactly what to which target?" Make abstract actions more concrete until they can be conveyed through image and sound.

---

## 11. Dimension ten: other characters need independent reasons to respond

### QA case: `train-96` / `oReact`

> **Context:** Jesse offered to help another person.
> **Question:** How would Others feel?
> **Correct:** `thankful`
> **Incorrect:** `caring and kind`; `ungrateful`

`caring and kind` describes the helper's traits, not the recipient's feelings.

### Script error

Every NPC immediately smiles, thanks S1, and cooperates after S1 acts, regardless of whether the NPC benefits, loses something, is in a hurry, or is suspicious.

### Plausible rewrite

- The receptionist sees S1's own umbrella blocking the door and gives a reminder as part of the job, rather than issuing an arbitrary command.
- S1 sees that the door is stuck, then apologizes and acts on the evidence rather than obeying simply because an NPC spoke.
- The scarf's owner confirms ownership before thanking S1 and taking it, rather than responding before knowing what the object is.

### Principle

Track each NPC's goals, tasks, information, gains, losses, and next step separately. Their response must follow their own reasoning, not act as an accessory to the protagonist's goal.

---

## 12. Dimension eleven: actions must produce traceable results

### QA case: `train-40` / `xEffect`

> **Context:** A doctor provided professional treatment to critically ill Quinn.
> **Question:** What will happen to Quinn?
> **Correct:** `get better`
> **Incorrect:** `be nervous`

Recovery is a physical result; nervousness is a mental state and cannot substitute for the treatment's effect.

### Script error

The receptionist concludes, "The entrance is safe now," but the image never shows the umbrella leaving the door track, the door closing, or the passage clearing.

### Plausible rewrite

After S1 lifts the umbrella, the unobstructed glass door closes continuously. S1 places the umbrella in the stand, the mat stays clear, and rain no longer enters. The environment's state proves the result.

### Principle

At each scene's end, record changes in information, object support, tasks, positions, risks, and relationships. If every state matches the opening, the scene usually has not advanced the story.

---

## 13. Dimension twelve: results must persist through the ending

### QA case: the pan-fire story

The original version resumes cooking soon after the lid smothers the fire, as if the accident never happened. The later part repeatedly emphasizes that nobody touches the lid, producing static repetition.

### Plausible rewrite

The trainee admits turning up the heat to brown the vegetables quickly. The affected pan stays covered while cooling. At an adjacent cold worktop, she places a spare lid beside the new pan before starting. The previous result becomes a prerequisite for the next action and demonstrates learning.

### Principle

Injury, knowledge, commitments, object states, and relationships cannot reset at chunk boundaries. Preserve a visible lasting consequence at the end rather than returning to the pre-story state.

---

## 14. Combined case A: the clinic umbrella stand

### Implausible version

- A blue umbrella is already on the mat, with no established owner.
- The receptionist asks a random visitor to handle an unfamiliar item, with no responsibility established.
- Nobody and nothing is obstructed, yet dialogue announces that the entrance is safe.
- Picking up, straightening, aligning, inserting, and releasing are split excessively without adding story information.

### Plausible version: about 20 seconds, two people only

```text
1. S1 closes their own wet umbrella and enters the clinic, laying it across the inside mat to take out a phone.
2. As the glass door swings back, the umbrella tip blocks it halfway open and rain blows into the entrance.
3. The receptionist points toward the entrance: "Sir, your umbrella is blocking the door. The stand is on the right."
4. S1 turns to see the stuck door: "Sorry, I'll put it away now."
5. S1 lifts their own umbrella and the glass door resumes closing.
6. S1 puts the umbrella into the stand to the door's right; the door closes fully and the mat and passage stay clear.
```

### Why it works

- The door's state provides visible risk and resolution without adding a character.
- S1 owns the umbrella, establishing responsibility.
- The receptionist's reminder follows their role and a visible problem.
- S1 corrects the problem based on evidence rather than mechanical obedience.
- The closing door and absence of incoming rain prove the result, rather than dialogue declaring it.

---

## 15. Combined case B: the red scarf at the bus stop

### Implausible version

- Narration alone declares ownership; S1 has no evidence.
- The woman suddenly approaches the boarding point before the bus arrives.
- After confirming ownership, she waits through an unnecessarily long handoff by S1.
- After receiving the scarf, she neither puts it away nor continues boarding; the ending proves only momentary possession.

### Plausible version: about 17 seconds

```text
1. The scarf is visibly looped through the woman's handbag handle.
2. The bus arrives and opens its door; she rises hurriedly and the scarf slips from the handle onto the bench.
3. S1 sees it happen and calls, "Ma'am, you dropped your red scarf!"
4. She touches the empty bag handle and her neck, confirming, "It's mine, thank you!"
5. Being closer to the bench, S1 picks up the scarf, walks two steps, and stops in front of her.
6. After taking it securely, she wraps it around her neck; S1 clears the boarding route.
7. She boards with the scarf and handbag, leaving the bench empty.
```

### Why it works

Ownership, loss, discovery, confirmation, pickup, handoff, and the next goal are all visible. The bus's arrival explains the haste and time pressure.

---

## 16. Combined case C: a small pan fire in cooking class

### Implausible version

- Flames appear without a cause.
- The trainee and classmate mechanically wait for the chef to finish speaking before acting.
- The trainee has no goal, mistake, request for help, or growth.
- The classmate covers the pan from directly above with bare hands, an unsuitable action.
- After extinguishing the fire, the scene only repeats waiting and shows no consequence for the characters.

### Plausible version: about 30 seconds

```text
1. Wanting to brown the vegetables quickly, the trainee checks the demonstration dish and turns the heat up from medium.
2. The oil hisses sharply, gray smoke rises, and a small localized flame appears in the pan; the trainee stops and calls for help.
3. A classmate instinctively reaches toward a water glass; the chef stops the reach and assigns turning off the heat and fetching the lid.
4. The trainee sets the wooden spoon down securely and turns off the heat; the classmate puts on heat-resistant gloves and takes the lid.
5. The chef instructs sliding the lid from the side; the trainee steps half a pace back to make room.
6. The classmate slides the lid over the pan to seal it, the flame disappears, and all three step back.
7. The trainee admits increasing the heat to brown the vegetables quickly.
8. The chef gives one piece of teaching feedback.
9. The trainee places a spare lid beside an adjacent cold pan before starting; the affected pan stays covered while cooling.
```

### Why it works

Action costs, professional competence, and responsibilities are clear. A mistaken impulse is corrected promptly. The result changes the pan's state, the trainee's knowledge, and the next operation.

### Complexity reminder

This version is already close to its 30-second budget. If it exceeds four dialogue turns or nine actions, first combine the chef's repetitive confirmations and remove decorative waiting, rather than removing the fire's cause, turning off the heat, sliding the lid, or the concluding growth.

---

## 17. Template for applying the cases to a new story

Complete this before generating a new story:

```text
Core event to preserve from the source:
Who S1 is and their immediate goal:
Why each existing NPC is present:
Initial holder or support of each critical object:
Why the trigger occurs now:
How each person knows what they know:
Who has responsibility, ability, and authority to act:
Minimum executable action chain:
Direct external result:
Character or relationship result:
How to make the result visible without adding a character:
How the ending proves that the result persists:
```

Final check: if the story seems unchanged after substituting identities, deleting the trigger, swapping roles, or rearranging time, its characters and causality are not yet integral to the script. Continue repairing it.

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

- More than 0 and no more than 60 seconds.
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

Example (shown in English):

```text
First-person POV. Continuing at the same library counter, I watch the approximately forty-five-year-old woman librarian place the completed library card on the counter and say in a calm, clear adult female voice, "Your library card is ready. Please keep it safe."
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

{
  "_pipeline": {"schema_version": "6.7", "stage": 1},
  "base_name": "forest_viewpoint_directions",
  "source_assessment": {
    "intended_event": "A hiker asks a trail guide how far the viewpoint is and continues in the indicated direction.",
    "hard_facts": ["Continuous first-person hiking viewpoint", "One guide answers the distance question", "The hiker continues uphill"],
    "repairs": ["Establish the guide before the question and show the route before departure"],
    "discarded_details": []
  },
  "story_contract": {
    "pov_role_id": "ego_hiker",
    "immediate_goal": "Learn the remaining distance to the viewpoint.",
    "visible_trigger": "The hiker sees a trail guide beside the uphill path.",
    "interaction_reason": "The guide is a credible nearby source of route information.",
    "decisive_response": "The guide answers and points up the same path.",
    "visible_result": "The hiker turns toward the indicated route and resumes walking.",
    "next_state": "The hiker continues uphill with the guide behind-left."
  },
  "roles": [
    {
      "role_id": "ego_hiker",
      "is_camera_wearer": true,
      "identity": "An adult man hiker and the only camera wearer.",
      "prompt_reference": "the adult male hiker",
      "goal": "Reach the viewpoint without taking a wrong branch.",
      "known_information": ["The viewpoint is uphill but the remaining distance is unknown."],
      "capability_and_authority": "Can walk the trail and ask for directions.",
      "possessions": ["small daypack"],
      "relationship": "A trail user speaking briefly with a guide.",
      "likely_next_action": "Continue along the indicated route."
    },
    {
      "role_id": "trail_guide",
      "is_camera_wearer": false,
      "identity": "An adult woman trail guide in a green outdoor jacket.",
      "prompt_reference": "the adult woman guide in a green outdoor jacket",
      "goal": "Help trail users follow the correct route.",
      "known_information": ["The viewpoint is ten minutes farther uphill."],
      "capability_and_authority": "Has local route knowledge and may provide directions.",
      "possessions": [],
      "relationship": "A guide assisting the hiker.",
      "likely_next_action": "Return attention to the trail after answering."
    }
  ],
  "objects": [],
  "information_evidence": [
    {"role_id": "ego_hiker", "fact": "The guide is available to answer.", "source": "sight", "learned_at_beat": 1, "resulting_action": "Stop and ask."},
    {"role_id": "ego_hiker", "fact": "The viewpoint is ten minutes uphill.", "source": "dialogue", "learned_at_beat": 3, "resulting_action": "Continue uphill."}
  ],
  "environment_requirements": [
    {
      "environment_id": "forest_viewpoint_path",
      "content": "A narrow dirt trail climbs gently through daytime forest, bordered by green shrubs and tall trees. The uphill continuation remains visible behind the guide under soft daylight and light wind."
    }
  ],
  "spatial_plan": {
    "camera_start": "Two meters downhill from the guide, facing uphill.",
    "stable_anchors": ["dirt trail", "green shrubs", "uphill continuation"],
    "route": ["approach guide", "stop two steps away", "pass on trail side", "continue uphill"],
    "terminal_composition": "The uphill trail is centered; the guide remains behind-left."
  },
  "dialogue": [
    {"speaker_role_id": "ego_hiker", "language": "English", "utterance": "How much farther is the viewpoint ahead?", "purpose": "Request the missing distance."},
    {"speaker_role_id": "trail_guide", "language": "English", "utterance": "It is another ten minutes on foot.", "purpose": "Supply distance and motivate travel."}
  ],
  "beats": [
    {"beat_id": 1, "duration_seconds": 3.0, "action_type": "navigation", "dominant_change": "Approach and stop at speaking distance.", "participants": ["ego_hiker", "trail_guide"], "environment_ids": ["forest_viewpoint_path"], "plan": "Walk uphill, decelerate, and stop two steps from the guide.", "end_state": "Camera faces the guide; uphill route remains behind her."},
    {"beat_id": 2, "duration_seconds": 2.5, "action_type": "manipulation", "dominant_change": "The hiker asks the distance.", "participants": ["ego_hiker", "trail_guide"], "environment_ids": ["forest_viewpoint_path"], "plan": "Remain stopped, ask one question, and let the guide listen.", "end_state": "Question is complete; guide faces the camera wearer."},
    {"beat_id": 3, "duration_seconds": 2.5, "action_type": "manipulation", "dominant_change": "The guide answers and points uphill.", "participants": ["ego_hiker", "trail_guide"], "environment_ids": ["forest_viewpoint_path"], "plan": "Listen while the guide answers and indicates the visible path.", "end_state": "Answer is complete; guide's hand identifies the route."},
    {"beat_id": 4, "duration_seconds": 2.0, "action_type": "navigation", "dominant_change": "The hiker resumes travel.", "participants": ["ego_hiker", "trail_guide"], "environment_ids": ["forest_viewpoint_path"], "plan": "Turn, pass the guide, and continue uphill.", "end_state": "The uphill trail is centered and forward motion resumes."}
  ],
  "render_policy": {
    "save_name": "forest_viewpoint_directions.mp4",
    "seed": 10001,
    "height": 544,
    "width": 960,
    "fps": 24,
    "num_inference_steps": 4,
    "control_signal": "camera_delta",
    "discrete_camera": true,
    "prompt_language": "English",
    "visual_style": "Naturalistic live-action cinematic style, continuous embodied eye-level viewpoint, with stable identities, spatial anchors, and actions",
    "non_diegetic_music": "N/A"
  }
}

## Optional reference images

The user message may include zero, one, or multiple reference images. Only Story generation inspects these images. Images are labeled `<Picture 1>`, `<Picture 2>`, etc. in supplied order, starting at 1. These exact labels identify the visual inputs in the downstream encoder; never renumber them by importance, order of appearance in the story, or filename.

Add a top-level `ref` array to the Story Decision: one nonempty caption string per image, in supplied order; use `[]` when there are no images. Begin each caption with its exact `<Picture N>` label and include its supplied filename. Describe the visible subject and whether it supplies a character, scene, object, or multiple subjects. Captions are for understanding and binding references, not replacements for image conditioning. Do not infer identity or unseen details from a filename alone; state uncertainty when necessary.

Bind relevant roles, objects, and environment_requirements to their exact `<Picture N>` references. For an image-grounded role, use a stable prompt_reference such as "the young man in <Picture 2>", with only enough additional description to distinguish subjects within that image. Retain image references in the bindings rather than replacing them with a long caption-derived appearance description. A scene and a character may come from different images; bind them separately. Do not force irrelevant references into the story. A person depicted in a story photograph is not physically present merely because a reference image depicts them.

In each existing environment requirement's descriptive text, explicitly bind the scene or its specific visible part to its image, e.g. "shop interior shown in <Picture 2>". A caption in `ref` alone is not a scene binding. When several images show different views or parts of one location, distinguish those views or parts in the existing descriptive fields; do not imply that every image applies to every camera view. Preserve these bindings when a story beat reuses that environment. Do not add schema fields for this mapping.

Preserve explicit story intent and the existing first-person/continuity rules. Record material conflicts or repairs in source_assessment. With no images, use `ref: []` and never invent `<Picture N>` references.

## Case study: allocate time to readable events, not equal-length slots

This example compares an original plan, a manually revised plan, and a proposed refinement informed by video frame inspection. Learn the allocation method; do not copy the setting, durations, or gestures into unrelated stories. The refinement has not yet been rendered. It adds no JSON fields and does not change the existing duration or dialogue limits.

### Source event and causal order

A first-person traveler pulls luggage toward a restaurant in a western town and asks whether it is Gray Wolf Bar. The young man answers that it serves food by day and is a bar at night. They exchange brief arrival/work questions. POV explains that someone important disappeared here, takes a worn photo from their own inner pocket and hands it over. The young man studies it and becomes serious; only then does POV ask whether he has seen her. He returns the photo, requests privacy, releases the restaurant door and walks toward the adjacent alley, inviting POV to follow. The girl in <Picture 1> appears inside the photograph; the young man uses <Picture 2>. Do not invent a last-seen location or treat his expression as confirmed recognition.

### Original 32-second plan versus manually revised 44-second plan

| Event | Original allocation | Manual allocation and reason |
|---|---|---|
| Approach and stop | 4 s | 4 s; establish the exterior alley and park luggage beside POV. |
| Ask about the bar | 3 s | 3.5 s; allow the complete question. |
| Answer and ask about arrival | 3.5 s | 4.5 s; longer utterance needs more time. |
| Confirm arrival / ask about work | 2.5 + 2.5 s | 1.5 + 1.5 s; brief replies do not need equal time to complex actions. |
| Explain the search, retrieve and offer photo | 4 s, with “Have you seen her?” prematurely merged into the explanation | 4 s explanation + 4 s retrieval/handoff; the question stays after viewing. |
| View photo and react | 3 s | 4 s including the subsequent short question; allow the reaction to be seen first. |
| Return photo | 3 s | 6 s including return, lowering the photo, looking back at the face and the privacy request. |
| Request privacy and release door | 3 s for the combined final utterance | 4 s for releasing, orienting and saying “Come with me. Let us talk outside.”; the privacy sentence occurs in the previous beat. |
| Leave toward alley | 3.5 s, mostly turning/gesturing | 7 s for actual leading, taking the luggage handle and following continuously. |

The original overloaded speech and hand actions and left the departure incomplete. The manual plan made these transitions more readable, but its 4-second retrieval/handoff still includes several sequential changes. It also preserves eight speaking beats (the last two sentences are separate deliveries), exceeding the default six-turn budget for this duration; seven dialogue-array entries do not make this six turns.

### Video observations and proposed refinement

The 44.125-second rendered video showed clearer luggage ownership, photo viewing and an actual walk into the alley. Remaining visible issues included sustained door-holding, the returned photo obscuring the face, and a pointing gesture performed by POV. The manual plan and H3 already required lowering the photo and assigned the gesture to the young man, so those failures are not proof that Story generation omitted the instructions. Avoid adding more simultaneous gestures as a remedy.

For a refinement compatible with the existing six-turn budget, omit the nonessential arrival/work exchange and record this repair in source_assessment. Keep the location answer, the search, the photo-dependent question and the privacy invitation. Do not merge across the photo reaction to save turns.

| Beat | Duration | Planned event and visible end state |
|---|---:|---|
| 1 | 4 s | Approach; park luggage upright by POV's right foot and release its handle. Establish the restaurant doorway and a separate exterior alley to its right. |
| 2 | 3.5 s | POV: “Excuse me, is this the Gray Wolf bar in town?” Stop at speaking distance. |
| 3 | 3 s | Young man: “We serve food here during the day. It is a bar at night.” Finish the answer; omit the redundant arrival/work questions. |
| 4 | 4 s | POV: “I am looking for someone. Someone very important to me went missing here.” Finish speaking before retrieval. |
| 5 | 3 s | Briefly look toward one's own coat, retrieve the worn photo and bring it into offering position. Do not invent folding/unfolding; no handoff yet. |
| 6 | 3 s | Offer the photo; the young man grasps it with his free hand before POV releases. POV hands withdraw and gaze returns to his face. |
| 7 | 4 s | He studies the photo and becomes serious; only after the reaction, POV asks “Have you seen her?” The photo stays below his face. |
| 8 | 7 s | He returns it; POV receives and lowers it below the main view, then looks back at his face. He quietly says “There are too many people here. This is not the place to discuss it.” End with the photo lowered. |
| 9 | 4 s | He releases the door, naturally turns toward the established alley and says “Come with me. Let us talk outside.” No additional pointing gesture is needed; his orientation and next movement show the route. |
| 10 | 7 s | He walks ahead; POV grasps the luggage handle and turns to follow, keeping the photo low. The restaurant and exterior alley retain their positions. |

Total: 42.5 seconds, 10 beats, six speaking beats (2, 3, 4, 7, 8, 9). The scene is slightly shorter overall while retrieval/handoff gains time: remove low-value dialogue rather than rush a critical interaction. Do not freeze the young man's arm in a rigid pose throughout the conversation; holding the door does not require repeated conspicuous gestures.

Before emitting a new plan, assign each utterance to its beat, estimate speech and sequential action/reaction time, and then sum durations. Reconcile object support and information-evidence beat IDs after any split or omission. An unrelated scene may need less or more time; neither 32, 44 nor 42.5 seconds is a target.

### Follow-up: problems still visible in the generated 41-second case

A later model-generated Story Decision used 41 seconds and 10 beats; its 41.292-second video showed a complete departure into the alley, but photo handling and spatial relationships still needed work. This was not a render of the exact 42.5-second proposal above. Frame inspection alone does not establish audio timing or prove that one stage caused every visual failure.

| Observed or documented issue | Story generation lesson |
|---|---|
| The generated plan added a folded photo and unfolding, although the source only specified a worn photo. Retrieval, unfolding and offering occupied 4 seconds. | Do not add a physical operation merely to elaborate appearance. Keep retrieval, supported handoff and the subsequent reaction readable; preserve required source operations when they actually exist. |
| Luggage appeared close to the young man despite the instruction to park it by POV's right foot. | Ownership was specified, but spatial execution failed. Establish it beside the camera wearer, nearer than the young man, clear of the doorway and route; do not force it into the center of every shot. |
| The returned photo again occupied the foreground and the young man's face was cropped, although the plan required lowering it. | State the completed transition: POV holds the photo below the main view, the other person has released it, and attention returns to the face before the next response. Do not treat a repeated instruction as proof of execution. |
| Approach/stop and turn/follow were each left as one Action generation control phase. | A Story generation beat may contain successive semantic events, but make their order and end states explicit. It is not a requirement that one beat become one downstream action. |

Retain uncertainty: the latest generated case again invented a last-seen location near the bar and asserted recognition. Neither is established by the source. Record omitted arrival/work dialogue as a repair rather than claiming that nothing was omitted. These content corrections and the refinements above are proposed improvements, not verified video fixes.
