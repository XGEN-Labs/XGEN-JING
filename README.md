https://github.com/user-attachments/assets/16ad3a85-d174-4947-92a6-d6ee4060d4fc

<h1 align="center">
  <img src="assets/xgen-logo.png" width="48" align="absmiddle" alt="XGEN logo">
  XGEN-JING: An Egocentric<br>
  Interactive Experience Model
</h1>
<p align="center">XGEN Team</p>

<p align="center">
  <a href="https://github.com/XGEN-Labs/XGEN-JING"><img src="https://img.shields.io/badge/GitHub-XGEN--JING-181717?logo=github&amp;logoColor=white" alt="GitHub"></a>
  <a href="https://huggingface.co/XGENlabs/XGEN-JING"><img src="https://img.shields.io/badge/Hugging_Face-Models-FFD21E?logo=huggingface&amp;logoColor=black" alt="Hugging Face"></a>
  <a href="https://xgenlabs.ai/gallery.html"><img src="https://img.shields.io/badge/Gallery-XGEN--JING-2563EB" alt="Gallery"></a>
  <a href="https://xgenlabs.ai/research.html"><img src="https://img.shields.io/badge/Blog-XGEN%20Labs-F97316" alt="Blog"></a>
  <img src="https://img.shields.io/badge/arXiv-Coming_Soon-B31B1B?logo=arxiv&amp;logoColor=white" alt="arXiv: Coming Soon">
</p>

---

We present **XGEN-JING**, an egocentric interactive experience model built on
[MiniMax-H3](https://github.com/MiniMax-AI/MiniMax-H3). Given actions, reference
images, and observation history, JING generates first-person video and audio for
navigation, object interaction, and conversation.

- **Camera control.** Explore everyday places and imagined worlds through
  keyboard-controlled movement.
- **Interaction and dialogue.** Guide object interactions and character
  conversations with text, with video and audio generated together.
- **Reference conditioning.** Combine character, object, and scene images to
  compose an experience and explore different actions from the same starting point.

This release provides **four-step bidirectional inference**, example cases, and
**Prompt skills**. The causal model and technical report are coming soon.

## 📋 Release Plan

- [x] **JING-Flash-v1** — Four-step bidirectional model.
- [x] **Inference code and examples** — Camera controls, reference images, and joint audio/video generation.
- [x] **[Prompt skills](prompt_skills/SKILL.md)** — Generate validated inference cases from stories and reference images.
- [ ] **Causal model** — Coming soon.
- [ ] **Technical report** — Coming soon.

## 🚀 Quick Start

### 1. Installation

Use Python 3.12 and a compatible CUDA environment. The demo has been validated on
**six H100 GPUs**: one for the text encoder, one for the video/audio VAEs, and four
for the DiT with sequence parallelism. FlashAttention-4 is the default backend.

```bash
git clone https://github.com/XGEN-Labs/XGEN-JING.git
cd XGEN-JING
python3 -m pip install -r requirements.txt
```

<details>
<summary>SGLang runtime and validated CUDA versions</summary>

Install [SGLang](https://github.com/sgl-project/sglang/tree/95140a7b0c9fc2f87a2a6cf6f6f0df8640a73174)
at commit `95140a7b0c9fc2f87a2a6cf6f6f0df8640a73174` separately. Keep the Diffusers
revision pinned in `requirements.txt`; SGLang's diffusion extra pins a different
version. The validated stack uses Torch 2.13.0+cu130, torchvision 0.28.0+cu130,
Triton 3.7.1, FA4 4.0.0b26, and SGLang kernel 0.4.7+cu130 from the
[CUDA 13 wheel index](https://sgl-project.github.io/whl/cu130/sglang-kernel/).

</details>

### 2. Model weights

JING Flash is built upon
[MiniMax-H3 Ref2VA](https://huggingface.co/MiniMaxAI/MiniMax-H3) and
[FlashGen](https://huggingface.co/Beidouqixing/minimax-h3-4step-lora-flashgen)
for a faster experience.

The demo loads the **JING-Flash-v1 transformer** from
[Hugging Face](https://huggingface.co/XGENlabs/XGEN-JING/tree/main/jing_flash_v1).
The text encoder, tokenizer, processor, video/audio VAEs, and schedulers come from
**Diffusers-format MiniMax-H3**.

Required model files are downloaded automatically on first use and reused from the
Hugging Face cache. Set `HF_HOME` to choose the cache location. No manual download
or weight directory is required. Repository IDs are configured in
[configs/base.yaml](configs/base.yaml).

### 3. Inference

```bash
python3 demo_bidirection.py check_config=true
bash demo.sh cases=examples/bakery_greeting.json
```

Results are saved to `examples/outputs/`.

<details>
<summary>Custom model paths and GPU selection</summary>

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3,4,5 bash demo.sh \
  model.h3=/path/to/MiniMax-H3 \
  model.transformer=/path/to/XGEN-JING \
  output.directory=/path/to/outputs
```

</details>

<details>
<summary>Write your own prompts and controls</summary>

Start from [the bakery example](examples/bakery_greeting.json). Each case combines
reference images with a sequence of prompts and controls. A prompt chunk uses one
control entry per repeated slice:

```json
{
  "prompt": "First-person view: approach the counter and greet the baker.",
  "repeat": 3,
  "control": ["w", "w,a", ""]
}
```

`w/s/a/d` control forward/backward/left/right movement. `"w,a"` combines two keys
in one slice; `""` applies no keys. Keep `control` the same length as `repeat`.
With the default layout, `num_frames = 17 * sum(repeat) + 5`. Reference images
are ordered and addressed as `<Picture 1>`, `<Picture 2>`, and so on, up to five.

</details>

### Prompt skills

Use **[Prompt skills](prompt_skills/README.md)** to turn a story and reference images
into a validated cases JSON file, ready to pass to `demo.sh`. It includes a
standalone guide and supports a configurable Chat Completions API.

## 🤝 Acknowledgments

We thank the **[MiniMax-H3 team](https://github.com/MiniMax-AI/MiniMax-H3)** for
opening their audio/video foundation model, and the
**[FlashGen team](https://huggingface.co/Beidouqixing/minimax-h3-4step-lora-flashgen)**
for their four-step acceleration work and model release.

We also thank [Diffusers](https://github.com/huggingface/diffusers),
[SGLang](https://github.com/sgl-project/sglang), and
[FlashAttention](https://github.com/Dao-AILab/flash-attention) for their open-source
infrastructure. See [NOTICE](NOTICE) for component attributions.

## License

XGEN-JING code and model weights are released under the
[MiniMax H3 Community License Agreement](LICENSE). Third-party components retain
their original licenses; see [NOTICE](NOTICE).
