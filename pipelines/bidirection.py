"""Four-step bidirectional audio/video inference."""

import gc
import json
import os
from datetime import timedelta
from functools import partial
from pathlib import Path
from types import SimpleNamespace

import torch
import torch.distributed as dist
from diffusers import (
    AutoencoderKLMiniMaxH3,
    AutoencoderKLMiniMaxH3Audio,
    MiniMaxH3Scheduler,
)
from diffusers.modular_pipelines import PipelineState
from diffusers.modular_pipelines.minimax_h3.decoders import (
    MiniMaxH3AudioDecodeStep,
    MiniMaxH3VideoDecodeStep,
)
from diffusers.modular_pipelines.minimax_h3.encoders import (
    MiniMaxH3KeyframeVaeEncoderStep,
    MiniMaxH3TextEncoderStep,
)
from diffusers.modular_pipelines.minimax_h3.packing import (
    prepare_keyframe_image,
    unpatchify_video_tokens,
)
from diffusers.utils import load_image
from diffusers.utils.export_utils import encode_video
from diffusers.video_processor import VideoProcessor
from models.attention import build_attention_groups
from models.packing import audio_endpoint, chunk_lengths, expand_slices, pack
from models.transformer import H3Transformer
from runtime.sglang_loader import (
    load_transformer, resolve_transformer, upstream_loader, validate_weights,
)
from tqdm.auto import tqdm
from transformers import (
    Qwen2TokenizerFast,
    Qwen3VLForConditionalGeneration,
    Qwen3VLProcessor,
)


def read_cases(config):
    path = Path(config["cases"])
    cases = json.loads(path.read_text())
    if not isinstance(cases, list) or not cases:
        raise ValueError("cases must be a non-empty JSON list")
    names = set()
    prepared = []
    allowed = {
        "name",
        "prompt",
        "control",
        "slices",
        "chunks",
        "save_name",
        "reference_images",
        "height",
        "width",
        "num_frames",
        "seed",
    }
    for index, case in enumerate(cases):
        if not isinstance(case, dict) or set(case) - allowed:
            raise ValueError(
                f"Case {index}: unknown fields (use chunks with repeat/control, or slices)"
            )
        settings = dict(config["generation"])
        settings["seed"] += index
        settings.update(
            {
                key: case[key]
                for key in ("height", "width", "num_frames", "seed")
                if key in case
            }
        )
        for key in ("height", "width", "num_frames"):
            if type(settings[key]) is not int or settings[key] <= 0:
                raise ValueError(f"Case {index}: {key} must be a positive integer")
        if settings["height"] % 32 or settings["width"] % 32:
            raise ValueError("Canvas must be divisible by 32")
        frames, lengths = chunk_lengths(
            settings["num_frames"], settings["first_chunk_size"]
        )
        slices = expand_slices(case, len(lengths))
        references = case.get("reference_images", [])
        if (
            not isinstance(references, list)
            or len(references) > settings["ref_image_slots"]
        ):
            raise ValueError("Invalid reference_images count")
        image_paths = []
        for reference in references:
            image_path = Path(reference)
            if not image_path.is_absolute() and not image_path.is_file():
                image_path = path.parent / image_path
            if not image_path.is_file():
                raise ValueError(f"Reference image does not exist: {image_path}")
            image_paths.append(str(image_path))
        save_name = case.get("save_name")
        if save_name is not None and (
            not isinstance(save_name, str) or Path(save_name).suffix.lower() != ".mp4"
        ):
            raise ValueError("save_name must be an MP4 path")
        name = case.get("name", Path(save_name).stem if save_name else f"case_{index + 1:02d}")
        if (
            not isinstance(name, str)
            or not name
            or name in (".", "..")
            or Path(name).name != name
            or name in names
        ):
            raise ValueError("Case names must be unique file basenames")
        names.add(name)
        settings["num_frames"] = frames
        prepared.append(
            {
                "name": name,
                "save_name": save_name,
                "settings": settings,
                "lengths": lengths,
                "slices": slices,
                "image_paths": image_paths,
            }
        )
    return prepared


def release_memory():
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


@torch.inference_mode()
def encode_cases(cases, config, architecture):
    root = config["model"]["h3"]
    dtype = getattr(torch, config["runtime"]["dtype"])
    text_device = torch.device(config["runtime"]["text_device"])
    vae_device = torch.device(config["runtime"]["vae_device"])
    components = SimpleNamespace(
        tokenizer=Qwen2TokenizerFast.from_pretrained(
            root, subfolder="tokenizer"
        ),
        processor=Qwen3VLProcessor.from_pretrained(
            root, subfolder="processor"
        ),
        text_encoder=Qwen3VLForConditionalGeneration.from_pretrained(
            root, subfolder="text_encoder",
            torch_dtype=dtype,
            attn_implementation="sdpa",
        )
        .eval()
        .requires_grad_(False)
        .to(text_device),
    )
    print(f"Text encoder loaded on {text_device}", flush=True)
    # Encoding finishes before the sharded DiT is loaded; the service GPU can be reused.
    for case in cases:
        settings = case["settings"]
        images = [
            prepare_keyframe_image(
                load_image(path),
                settings["height"],
                settings["width"],
                stretch=(index == 0),
            )
            for index, path in enumerate(case["image_paths"])
        ]
        case["images"] = images
        case["text_bank"] = {}
        for prompt in dict.fromkeys(item["prompt"] for item in case["slices"]):
            embeds, tags = MiniMaxH3TextEncoderStep.encode_prompt(
                components,
                prompt,
                images=images if settings["text_encoder_reference_images"] else None,
                device=text_device,
                dtype=dtype,
            )
            case["text_bank"][prompt] = (embeds.cpu(), tags.cpu())
            print(f"{case['name']}: encoded prompt {len(case['text_bank'])}", flush=True)
    del components
    release_memory()
    vae = None
    if any(case["images"] for case in cases):
        vae = (
            AutoencoderKLMiniMaxH3.from_pretrained(
                root, subfolder="vae", torch_dtype=torch.float32
            )
            .eval()
            .to(vae_device)
        )
        vae.enable_tiling()
        print(f"Reference VAE loaded on {vae_device}", flush=True)
    patch = tuple(architecture["patch_size"])
    for case in cases:
        settings = case["settings"]
        height, width = settings["height"] // 16, settings["width"] // 16
        frames = sum(case["lengths"])
        case["references"] = []
        for image in case.pop("images"):
            rows = MiniMaxH3KeyframeVaeEncoderStep.encode_keyframes(
                SimpleNamespace(vae=vae, patch_size=patch),
                [image],
                device=vae_device,
            )
            case["references"].append(
                unpatchify_video_tokens(
                    rows,
                    1,
                    image.height // 16,
                    image.width // 16,
                    architecture["in_channels"],
                    patch,
                )[0].cpu()
            )
        generator = torch.Generator(device="cpu").manual_seed(settings["seed"])
        audio_generator = torch.Generator(device="cpu").manual_seed(
            settings["seed"] + 1
        )
        case["video"] = (
            torch.randn(
                frames,
                architecture["in_channels"],
                height,
                width,
                generator=generator,
                dtype=torch.float32,
            )
            .permute(1, 0, 2, 3)
            .contiguous()
        )
        case["audio"] = (
            torch.randn(
                audio_endpoint(frames),
                2,
                architecture["audio_in_channels"],
                generator=audio_generator,
                dtype=torch.float32,
            )
            .permute(1, 0, 2)
            .contiguous()
        )
    del vae
    release_memory()
    return cases


@torch.inference_mode()
def denoise(
    model, packed, settings, video_scheduler, audio_scheduler, show_progress=False
):
    mask = build_attention_groups(packed.owners, packed.is_media)
    # Four distilled noise levels plus the terminal clean endpoint.
    base_sigmas = torch.tensor([1.0, 0.7, 0.4, 0.15, 0.0], dtype=torch.float32)
    steps = 4
    for scheduler in (video_scheduler, audio_scheduler):
        # Explicit sigmas are already shifted; the scheduler uses them verbatim.
        shift = scheduler.shift
        sigmas = shift * base_sigmas / (1 + (shift - 1) * base_sigmas)
        scheduler.set_timesteps(sigmas=sigmas, device=packed.video.device)
    if (
        len(video_scheduler.timesteps) != steps
        or len(audio_scheduler.timesteps) != steps
    ):
        raise RuntimeError(
            "Unexpected H3 scheduler semantics: expected one forward per requested step"
        )
    for vt, at in tqdm(
        zip(video_scheduler.timesteps, audio_scheduler.timesteps, strict=True),
        total=steps,
        disable=not show_progress,
    ):
        times, indices = packed.timesteps(vt, at, settings["reference_timestep"])
        video_prediction, audio_prediction = model(packed, times, indices, mask)
        start = packed.output_video_offset
        packed.video[:, start:] = video_scheduler.step(
            video_prediction[:, start:].float(),
            vt,
            packed.video[:, start:].float(),
            return_dict=False,
        )[0]
        packed.audio[:] = audio_scheduler.step(
            audio_prediction.float(), at, packed.audio.float(), return_dict=False
        )[0]
    if not torch.isfinite(packed.video).all() or not torch.isfinite(packed.audio).all():
        raise FloatingPointError("Non-finite generated latents")
    return packed.video[
        0, packed.output_video_offset :
    ].cpu(), packed.audio_channel_major().cpu()


@torch.inference_mode()
def decode(video_rows, audio_rows, case, architecture, config):
    root = config["model"]["h3"]
    device = torch.device(config["runtime"]["vae_device"])
    vae = (
        AutoencoderKLMiniMaxH3.from_pretrained(
            root, subfolder="vae", torch_dtype=torch.float32
        )
        .eval()
        .to(device)
    )
    vae.enable_tiling()
    audio_vae = (
        AutoencoderKLMiniMaxH3Audio.from_pretrained(
            root, subfolder="audio_vae", torch_dtype=torch.float32
        )
        .eval()
        .to(device)
    )
    settings = case["settings"]
    components = SimpleNamespace(
        _execution_device=device,
        vae=vae,
        audio_vae=audio_vae,
        vae_latent_channels=architecture["in_channels"],
        patch_size=tuple(architecture["patch_size"]),
        audio_sampling_rate=audio_vae.config.sampling_rate,
        video_processor=VideoProcessor(vae_scale_factor=16, do_normalize=False),
    )
    state = PipelineState()
    for key, value in {
        "latents": video_rows.to(device),
        "audio_latents": audio_rows.to(device),
        "num_condition_video_rows": 0,
        "num_condition_audio_rows": 0,
        "num_latent_frames": sum(case["lengths"]),
        "num_audio_latents": audio_endpoint(sum(case["lengths"])),
        "latent_height": settings["height"] // 16,
        "latent_width": settings["width"] // 16,
        "output_type": "pt",
    }.items():
        state.set(key, value)
    _, state = MiniMaxH3VideoDecodeStep()(components, state)
    _, state = MiniMaxH3AudioDecodeStep()(components, state)
    video, audio = state.get("videos")[0].cpu(), state.get("audio")[0].cpu()
    if not torch.isfinite(video).all() or not torch.isfinite(audio).all():
        raise FloatingPointError("Non-finite decoded media")
    output_path = (
        Path(case["save_name"]) if case.get("save_name")
        else Path(config["output"]["directory"]) / f"{case['name']}.mp4"
    )
    if case.get("save_name") and output_path.parent == Path("."):
        output_path = Path(config["output"]["directory"]) / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frames = video.permute(0, 2, 3, 1).mul(255).round().clamp(0, 255).to(torch.uint8)
    encode_video(
        frames,
        fps=24,
        output_path=str(output_path),
        audio=audio,
        audio_sample_rate=state.get("sampling_rate"),
    )
    metadata = {
        "settings": settings,
        "slice_lengths": case["lengths"],
        "slices": case["slices"],
        "fps": 24,
        "audio_sample_rate": state.get("sampling_rate"),
    }
    metadata_path = output_path.with_suffix(".settings.json" if case.get("save_name") else ".json")
    metadata_path.write_text(json.dumps(metadata, indent=2))
    if config["output"]["save_latents"]:
        from safetensors.torch import save_file

        save_file(
            {"video": video_rows.contiguous(), "audio": audio_rows.contiguous()},
            str(output_path.with_suffix(".safetensors")),
        )
    del components, vae, audio_vae, state
    release_memory()


def rank_zero_call(fn, group):
    """Propagate preparation/export failures so peers do not wait at a barrier."""
    result = [None]
    if dist.get_rank() == 0:
        try:
            result[0] = (True, fn())
        except Exception as error:  # noqa: BLE001 - peers must receive failures before their collective
            result[0] = (False, f"{type(error).__name__}: {error}")
    dist.broadcast_object_list(result, src=0, group=group)
    ok, value = result[0]
    if not ok:
        raise RuntimeError(value)
    return value


def run(config):
    if not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA is unavailable; multi-GPU inference requires a working NVIDIA driver"
        )
    local_rank = int(os.environ.get("LOCAL_RANK", "0"))
    world_size = int(os.environ.get("WORLD_SIZE", "1"))
    if world_size < 2:
        raise ValueError(
            "Launch demo.sh with NPROC_PER_NODE >= 2 for weight sharding"
        )
    offset = config["runtime"]["dit_device_offset"]
    if offset + world_size > torch.cuda.device_count():
        raise ValueError("Not enough visible GPUs for the configured DiT ranks")
    service_devices = [torch.device(config["runtime"][key]) for key in ("text_device", "vae_device")]
    for service in service_devices:
        if service.type == "cuda" and (
            service.index is None or service.index >= torch.cuda.device_count()
            or offset <= service.index < offset + world_size
        ):
            raise ValueError("Text encoder and VAE must use explicit GPUs outside the DiT ranks")
    if service_devices[0].type == "cuda" and service_devices[0] == service_devices[1]:
        raise ValueError("Text encoder and VAE must use separate GPUs")
    upstream_loader()
    device_index = config["runtime"]["dit_device_offset"] + local_rank
    torch.cuda.set_device(device_index)
    device = torch.device("cuda", device_index)
    print(f"DiT rank {local_rank}: {device}, SP={os.environ.get('WORLD_SIZE')}; "
          f"text={config['runtime']['text_device']}, VAE={config['runtime']['vae_device']}", flush=True)
    dist.init_process_group("nccl", timeout=timedelta(hours=2))
    try:
        host_group = dist.new_group(backend="gloo", timeout=timedelta(hours=2))
        source = rank_zero_call(partial(resolve_transformer, config["model"]), host_group)
        config["model"]["transformer"] = source
        config["model"]["transformer_subfolder"] = None
        architecture = H3Transformer.load_config(source)

        def prepare():
            print("Validating transformer tensors", flush=True)
            validate_weights(source, architecture)
            return encode_cases(read_cases(config), config, architecture)

        cases = rank_zero_call(prepare, host_group)
        if dist.get_rank() == 0:
            print("Encoding complete; loading sharded DiT", flush=True)
        model = load_transformer(config, device, dist.get_world_size()).eval()
        print(f"DiT rank {local_rank}: weights loaded on {device}", flush=True)
        root = config["model"]["h3"]
        video_scheduler = MiniMaxH3Scheduler.from_pretrained(
            root, subfolder="scheduler"
        )
        audio_scheduler = MiniMaxH3Scheduler.from_pretrained(
            root, subfolder="audio_scheduler"
        )
        for case in cases:
            packed = pack(case, architecture, case["settings"], device)
            if dist.get_rank() == 0:
                print(f"{case['name']}: {len(packed.token_tags)} tokens; starting 4 steps", flush=True)
            video, audio = denoise(
                model,
                packed,
                case["settings"],
                video_scheduler,
                audio_scheduler,
                show_progress=dist.get_rank() == 0,
            )
            del packed
            release_memory()
            rank_zero_call(
                partial(decode, video, audio, case, architecture, config), host_group
            )
            if dist.get_rank() == 0:
                print(f"Saved {case['name']}.mp4", flush=True)
    finally:
        dist.destroy_process_group()
