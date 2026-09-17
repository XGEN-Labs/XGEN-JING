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
- Render at 24 FPS with four denoising steps. Height and width must be positive multiples of 32. Render policy contains every value Compilation needs. Jing controls translation with WASD; in-place view rotation belongs in action prose, not additional control keys.
- Render policy uses `control_signal: "camera_delta"` and `discrete_camera: true`; Action generation will convert the spatial plan into a required per-repeat discrete control schedule.

Do not include final H3 prompts, S markers, `<d>` wrappers, chunks, or repeats in Story Decision. Those belong downstream.

# Script generation logic: principles grounded in concrete cases

本文将 原始问答对比材料转化为60秒内第一人称剧本的生成逻辑。使用时不要只记住结论；必须理解 case 中“为什么正确项比干扰项更适合当前角色、时间和问题类型”，再把这种关系迁移到新故事。

## 1. 使用方法

每个 case 按同一顺序分析：

```text
原始情境与问题
→ 正确项解决了什么逻辑约束
→ 错误项偷换了什么维度
→ 剧本中会表现为什么问题
→ 60秒内如何修复成可见行动
```

不要复制人物名或表面动作。应抽取角色、信息、时间、因果和状态变化结构。

---

## 2. 维度一：语义功能必须一致

### QA case：`train-17` / `xWant`

> **Context:** Ash rode hard and put away his wet clothes to let them dry for a few hours.
> **Question:** What will Ash want to do next?
> **数据标注答案:** `lazy`

这是一个应当拒绝的噪声 case。问题要求“下一步行动”，`lazy` 却是属性或状态，无法成为可执行动作。

### 剧本中的错误

```text
火被扑灭后，学员接下来变得内疚。
```

“内疚”是心理反应，不是下一步行动；视频也无法把它直接当成动作生成。

### 合理改写

```text
火被盖灭后，学员低头看向被自己调高的旋钮，承认错误，并在下一只冷锅旁先放好锅盖。
```

这里依次出现：心理外化、语言行动和学习后的下一步行动。

### Principle

给 action list 中的每个阶段标记主要功能：`MOTIVE / PRECONDITION / ACTION / EFFECT / EMOTION / NEXT_ACTION`。如果一个 description 无法落实为当前功能，应重写而不是用形容词填充。

---

## 3. 维度二：角色归属必须正确

### QA case：`train-54` / `oWant`

> **Context:** Taylor saved other people's teeth from decay by providing good toothpaste.
> **Question:** What will Others want to do next?
> **Correct:** `thank Taylor`
> **Incorrect:** `teach them how to floss`; `teach them how to use mouthwash`

正确项属于受益者的社会回应。错误项把帮助者的教育任务转移给接受帮助的人，造成角色职责倒置。

### 剧本中的错误

前台要求随机访客收拾一把来历不明的雨伞，但没有说明雨伞属于谁、访客为何负责。访客立即服从，就像工具人。

### 合理改写

先展示S1把自己的湿伞横放在门垫上。玻璃门因此无法闭合，前台提醒：“先生，您的伞挡住门了。”S1收起自己的伞。所有权、责任和行动主体一致。

### Principle

每个事件都要标记：发起者、对象、所有者、受益者、受损者、知情者和责任者。一个角色不能只因为离物体最近就自动获得处理责任。

---

## 4. 维度三：时间顺序必须成立

### QA case：`train-2` / `xWant`

> **Context:** Remy was on the water and had baited the hook.
> **Question:** What will Remy want to do next?
> **Correct:** `cast the line`
> **Incorrect:** `put the boat in the water`; `invite Kai out on the boat`

错误项并非永远错误，而是在当前时间点已经太迟。

### 剧本中的错误

人物已经走到公交车门前，下一段才第一次展示公交车驶来；或者围巾完成交还之后，才补拍它如何掉落。

### 合理改写

```text
公交驶近并开门
→ 女乘客匆忙起身
→ 围巾从袋把滑落
→ S1看到后提醒
→ 女乘客停下确认
```

### Principle

故事展示顺序可以省略装饰，但不能省略使后续反应成立的触发。每个 action 必须在 `BEFORE / DURING / AFTER / NEXT` 中占据正确位置。

---

## 5. 维度四：因果方向不能倒置

### QA case：`train-76` / `xEffect`

> **Context:** Taylor received the winning lottery ticket and won the jackpot.
> **Question:** What will happen to Taylor?
> **Correct:** `Have more money than before`
> **Incorrect:** `Buy more lottery tickets next time`

财富增加是已经发生的直接结果；继续买彩票只是可能的后续行为。

### 剧本中的错误

```text
前台说“门口安全了”，所以S1把雨伞放进架子。
```

实际因果应当是S1移走雨伞，门正常关闭，入口才恢复安全。

### 合理改写

```text
雨伞挡住玻璃门
→ 前台指出问题
→ S1移走雨伞
→ 玻璃门完整关闭
→ 雨水不再吹进入口
```

### Principle

对每个连接使用“因为A，所以B”测试。台词可以提示原因，但不能代替造成结果的物理行动。

---

## 6. 维度五：动机必须足以解释动作

### QA case：`train-15` / `xIntent`

> **Context:** Austin saw a purse on top of a moving car and ran alongside to get the driver's attention.
> **Question:** Why did Austin do this?
> **Correct:** `help another person`
> **Incorrect:** `be nice`; `practice for a marathon`

`practice for a marathon` 只能解释跑步，不能解释钱包、汽车和提醒司机；`be nice` 又过于宽泛。

### 剧本中的错误

随机访客听前台一句话，就花多个动作处理陌生物品；或者陌生人冒高风险帮助别人，却没有时间压力、职责或关系依据。

### 合理改写

让物品明确属于S1，或让S1亲眼看见它从对方手中掉落。低成本帮助只需要即时可见问题；高成本帮助还需要更强关系、职责或风险理由。

### Principle

动机必须解释：为什么是这个对象、为什么现在、为什么用这种方式、为什么愿意承担这个成本。

---

## 7. 维度六：行动前提必须完备

### QA case：`train-26` / `xNeed`

> **Context:** Aubrey understood the teacher's question and answered.
> **Question:** What did Aubrey need beforehand?
> **Correct:** `know the information`
> **Incorrect:** `ask for a gold star`; `skip her class`

正确回答知识问题需要事先掌握信息。索要奖励是事后行为，逃课则削弱前提。

### 剧本中的错误

同学突然知道如何处理油锅火灾、突然拿到锅盖，或者S1在没看见伞架的情况下准确走向伞架。

### 合理改写

- 第一段就把锅盖和隔热手套建立在固定架上。
- 主厨作为专业角色给出简短分工。
- 在人物移动前，让目的地先进入视野边缘。

### Principle

关键动作前检查：知道吗、会做吗、有工具吗、有权限吗、够得着吗。越能直接解决核心问题的能力和道具，越应提前建立。

---

## 8. 维度七：人物信息必须可达

### QA case：红围巾原剧本

原剧本一开始只展示一条红围巾放在长椅上，却直接在叙述中声明它属于绿衣女人。S1没有看到归属证据，却说：“您的红围巾落在长椅上了。”

这不是画面可获得的信息，而是作者信息。

### 合理改写

第一段展示红围巾穿绕在女人的手提袋把手上。公交到站后，围巾从袋把滑落到长椅，整个过程在S1视野内发生。此后S1准确喊“您的围巾掉了”便有可靠信息来源。

如果无法展示滑落，则应改问：

> “女士，这条红围巾是您的吗？”

### Principle

为每项判断记录：人物需要知道什么、信息来自视觉/声音/对话/既往身份中的哪一种、何时获得、获得后采取什么动作。人物不能拥有导演层的隐藏事实。

---

## 9. 维度八：情绪必须匹配目标和时间

### QA case：`train-22` / `xReact`

> **Context:** Quinn finally found a puppy missing for a week.
> **Question:** How would Quinn feel?
> **Correct:** `very relieved`
> **Incorrect:** `excited`; `very excited`

兴奋和宽慰都是正向情绪，但失而复得的核心机制是持续风险解除。

### 剧本中的错误

人物发现失物后只机械说“谢谢”，或者危险解除后仍保持完全相同的惊恐姿势。

### 合理改写

女乘客先检查空袋把和颈部，意识到围巾确实遗失；接稳并围回颈间后，肩膀放松、向S1点头，再继续登车。情绪变化依赖确认和结果，而不是提前出现。

### Principle

情绪由人物主观理解产生：他认为谁让自己的哪个目标发生了什么变化。用姿势、动作节奏、距离和下一项选择外化，不要只写情绪标签。

---

## 10. 维度九：下一步行动必须具体并连续

### QA case：`train-8` / `xWant`

> **Context:** Quinn wanted to help clean a messy room.
> **Question:** What will Quinn want to do next?
> **Correct:** `Pick up the dirty clothes`
> **Incorrect:** `help out a friend`

`help out a friend` 只重复总体目标；捡脏衣服才是可执行的下一步。

### 剧本中的错误

```text
S1意识到门口不安全，于是开始处理问题。
```

### 合理改写

```text
S1把手机放回口袋，转身走回地垫，俯身握住自己雨伞的弯柄，将它完整提离门轨。
```

### Principle

用“谁具体用什么，对什么做了什么？”测试 action description。无法被镜头和声音表现的抽象动作必须继续具体化。

---

## 11. 维度十：他人回应必须有独立逻辑

### QA case：`train-96` / `oReact`

> **Context:** Jesse offered to help another person.
> **Question:** How would Others feel?
> **Correct:** `thankful`
> **Incorrect:** `caring and kind`; `ungrateful`

`caring and kind` 是对帮助者的属性判断，不是受助者的感受。

### 剧本中的错误

所有NPC在S1行动后都立即微笑、感谢并配合；无论他们是否受益、受损、着急或怀疑。

### 合理改写

- 前台看到S1自己的伞挡门，因此履行岗位职责提醒，而不是无缘无故命令。
- S1看到门确实被卡住，因此道歉并处理，而不是因为NPC说话就服从。
- 围巾主人先确认归属，再感谢并接取，而不是在不知道物品是什么时立即回应。

### Principle

为NPC分别记录目标、任务、信息、得失和下一步。NPC的回应必须属于NPC，而不是主角目标的附属动画。

---

## 12. 维度十一：行动必须产生可追踪结果

### QA case：`train-40` / `xEffect`

> **Context:** A doctor provided professional treatment to critically ill Quinn.
> **Question:** What will happen to Quinn?
> **Correct:** `get better`
> **Incorrect:** `be nervous`

好转是身体结果；紧张是心理状态，不能替代治疗效果。

### 剧本中的错误

前台最后说“门口安全了”，但画面没有显示雨伞离开门轨、门关闭或通道恢复。

### 合理改写

S1提起雨伞后，玻璃门失去阻挡并连续闭合；S1把伞放入架内，地垫保持空出，入口不再进雨。结果通过环境状态证明。

### Principle

每场结束填写状态差：信息、物体支持、任务、位置、风险和关系分别改变了什么。若所有状态都与开场相同，该场通常没有推进故事。

---

## 13. 维度十二：结果必须延续到结尾

### QA case：油锅故事

原版本在锅盖灭火后很快恢复备餐，像事故从未发生；后半段又反复强调无人碰盖，形成静态重复。

### 合理改写

学员承认自己为快速上色调高火力。事故锅继续密封冷却；她移到相邻冷台面时，先把备用锅盖放在新锅旁。上一事件的结果转化成下一行动的前提，表现真正学习。

### Principle

伤害、知识、承诺、物体状态和关系变化不能在chunk边界重置。结尾应保留一个可见的长期后果，而不是恢复到故事开始前。

---

## 14. 综合 case A：诊所雨伞架

### 不合理版本

- 蓝伞一开始就在门垫上，所有者不明。
- 前台要求随机访客处理陌生物品，责任关系缺失。
- 没有人或环境受到阻碍，却用台词宣布“门口安全了”。
- 拾取、转正、对准、插入、松手被过度拆分，故事没有新信息。

### 约20秒、仅两人的合理版本

```text
1. S1收起自己的湿伞进入诊所，为拿手机把伞横放在门内地垫。
2. 玻璃门回弹时被伞尖挡住，停在半开位置，雨点吹进入口。
3. 前台指向入口：“先生，您的伞挡住门了，伞架就在右边。”
4. S1回头看见被卡住的门：“抱歉，我马上收好。”
5. S1提起自己的伞，玻璃门恢复闭合。
6. S1把伞放入门右侧伞架；门完全关闭，地垫和通道保持空出。
```

### 为什么合理

- 不新增人物也能用门的状态形成可见风险和结果。
- 伞属于S1，责任明确。
- 前台基于岗位和可见问题提醒。
- S1基于证据改正，不是机械服从。
- 终局由门关闭和入口不再进雨证明，而不是台词宣布。

---

## 15. 综合 case B：公交站红围巾

### 不合理版本

- 围巾归属仅由叙述声明，S1没有证据。
- 公交尚未到站，女人却突然走向乘车点。
- 女人确认后站着等待S1完成冗长手递手动作，行动成本偏高。
- 拿到围巾后没有收好或继续乘车，结局只证明瞬时握持。

### 约17秒合理版本

```text
1. 围巾可见地穿绕在女人的手提袋把手上。
2. 公交到站开门；女人匆忙起身，围巾从袋把滑落长椅。
3. S1亲眼看到并呼喊：“女士，您的红围巾掉了！”
4. 女人摸空袋把和颈部，确认：“是我的，谢谢！”
5. S1因离长椅更近而拾起围巾，走两步停在她面前。
6. 女人接稳后围回颈间，S1让开乘车路线。
7. 女人携围巾和手提袋登车，长椅为空。
```

### 为什么合理

归属、遗落、发现、确认、拾取、交接和后续目标全部可见；公交到站解释了匆忙与时间压力。

---

## 16. 综合 case C：烹饪课油锅小火

### 不合理版本

- 火焰无因出现。
- 学员和同学机械等待主厨说完才行动。
- 学员没有目标、失误、求助或成长。
- 同学从正上方徒手扣盖，动作不理想。
- 灭火后只重复等待，事件没有人物后果。

### 约30秒合理版本

```text
1. 学员想让蔬菜快速上色，对照示范菜后把火从中档调高。
2. 油声变尖、灰烟升起、锅内出现局限小火；学员停手并呼救。
3. 同学下意识伸向水杯；主厨制止并分工关火、取盖。
4. 学员放稳木勺并关火；同学戴隔热手套取盖。
5. 主厨提示从侧面滑盖；学员退半步让路。
6. 同学滑盖密封，火光消失，三人退开。
7. 学员承认自己急于上色而调高火力。
8. 主厨给出一次教学反馈。
9. 学员在相邻冷锅旁先放好备用锅盖，事故锅继续密封冷却。
```

### 为什么合理

行动成本、专业能力和角色分工明确；错误冲动被及时纠正；结果同时改变锅的状态、学员的知识和下一次操作。

### 复杂度提醒

该版本已接近30秒上限。如果对话超过四轮或action超过九个，应优先合并主厨的重复确认、删除装饰性等待，而不是删掉起火原因、关火、滑盖或终局成长。

---

## 17. 从 case 到新故事的迁移模板

生成新故事前填写：

```text
源故事希望保留的核心事件：
S1是谁、当前目标是什么：
现有NPC分别为什么在场：
关键物品最初由谁持有或支撑：
触发为何现在发生：
每个人凭什么知道：
谁有责任、能力和权限行动：
最小可执行行动链：
直接外部结果：
人物或关系结果：
无需新增人物时如何让结果可见：
结尾如何证明结果仍持续：
```

最终检查：如果替换人物身份、删除触发、交换角色或打乱时间顺序后故事仍看似不变，说明人物和因果尚未真正进入剧本，需要继续修复。

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
      "prompt_reference": "成年男性徒步者",
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
      "prompt_reference": "绿色户外夹克的成年女性向导",
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
    {"speaker_role_id": "ego_hiker", "language": "Chinese", "utterance": "前面的观景台还有多远？", "purpose": "Request the missing distance."},
    {"speaker_role_id": "trail_guide", "language": "Chinese", "utterance": "再走十分钟就到了。", "purpose": "Supply distance and motivate travel."}
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
    "prompt_language": "Chinese",
    "visual_style": "自然写实真人电影感，连续具身眼平视角，身份、空间锚点与动作保持稳定",
    "non_diegetic_music": "N/A"
  }
}

## Optional reference images

The user message may include zero, one, or multiple reference images. Only Story generation inspects these images. Images are labeled `<Picture 1>`, `<Picture 2>`, etc. in supplied order, starting at 1. These exact labels identify the visual inputs in the downstream encoder; never renumber them by importance, order of appearance in the story, or filename.

Add a top-level `ref` array to the Story Decision: one nonempty caption string per image, in supplied order; use `[]` when there are no images. Begin each caption with its exact `<Picture N>` label and include its supplied filename. Describe the visible subject and whether it supplies a character, scene, object, or multiple subjects. Captions are for understanding and binding references, not replacements for image conditioning. Do not infer identity or unseen details from a filename alone; state uncertainty when necessary.

Bind relevant roles, objects, and environment_requirements to their exact `<Picture N>` references. For an image-grounded role, use a stable prompt_reference such as "the young man in <Picture 2>" or "<Picture 2>中的青年", with only enough additional description to distinguish subjects within that image. Retain image references in the bindings rather than replacing them with a long caption-derived appearance description. A scene and a character may come from different images; bind them separately. Do not force irrelevant references into the story. A person depicted in a story photograph is not physically present merely because a reference image depicts them.

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
| Explain the search, retrieve and offer photo | 4 s, with “你见过她吗？” prematurely merged into the explanation | 4 s explanation + 4 s retrieval/handoff; the question stays after viewing. |
| View photo and react | 3 s | 4 s including the subsequent short question; allow the reaction to be seen first. |
| Return photo | 3 s | 6 s including return, lowering the photo, looking back at the face and the privacy request. |
| Request privacy and release door | 3 s for the combined final utterance | 4 s for releasing, orienting and saying “跟我来，我们出去说。”; the privacy sentence occurs in the previous beat. |
| Leave toward alley | 3.5 s, mostly turning/gesturing | 7 s for actual leading, taking the luggage handle and following continuously. |

The original overloaded speech and hand actions and left the departure incomplete. The manual plan made these transitions more readable, but its 4-second retrieval/handoff still includes several sequential changes. It also preserves eight speaking beats (the last two sentences are separate deliveries), exceeding the default six-turn budget for this duration; seven dialogue-array entries do not make this six turns.

### Video observations and proposed refinement

The 44.125-second rendered video showed clearer luggage ownership, photo viewing and an actual walk into the alley. Remaining visible issues included sustained door-holding, the returned photo obscuring the face, and a pointing gesture performed by POV. The manual plan and H3 already required lowering the photo and assigned the gesture to the young man, so those failures are not proof that Story generation omitted the instructions. Avoid adding more simultaneous gestures as a remedy.

For a refinement compatible with the existing six-turn budget, omit the nonessential arrival/work exchange and record this repair in source_assessment. Keep the location answer, the search, the photo-dependent question and the privacy invitation. Do not merge across the photo reaction to save turns.

| Beat | Duration | Planned event and visible end state |
|---|---:|---|
| 1 | 4 s | Approach; park luggage upright by POV's right foot and release its handle. Establish the restaurant doorway and a separate exterior alley to its right. |
| 2 | 3.5 s | POV: “不好意思，这里就是镇上的灰狼酒吧吗？” Stop at speaking distance. |
| 3 | 3 s | Young man: “这里白天卖饭，晚上才是酒吧。” Finish the answer; omit the redundant arrival/work questions. |
| 4 | 4 s | POV: “找人。一个对我很重要的人在这里失踪了。” Finish speaking before retrieval. |
| 5 | 3 s | Briefly look toward one's own coat, retrieve the worn photo and bring it into offering position. Do not invent folding/unfolding; no handoff yet. |
| 6 | 3 s | Offer the photo; the young man grasps it with his free hand before POV releases. POV hands withdraw and gaze returns to his face. |
| 7 | 4 s | He studies the photo and becomes serious; only after the reaction, POV asks “你见过她吗？” The photo stays below his face. |
| 8 | 7 s | He returns it; POV receives and lowers it below the main view, then looks back at his face. He quietly says “这里人太多，不是谈这件事的地方。” End with the photo lowered. |
| 9 | 4 s | He releases the door, naturally turns toward the established alley and says “跟我来，我们出去说。” No additional pointing gesture is needed; his orientation and next movement show the route. |
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
