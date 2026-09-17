"""Load public checkpoint tensors through SGLang's sharded inference loader."""

import json
from pathlib import Path

import torch
from diffusers.utils.hub_utils import _get_checkpoint_shard_files, _get_model_file
from models.transformer import H3Transformer
from safetensors import safe_open

SGLANG_COMMIT = "95140a7b0c9fc2f87a2a6cf6f6f0df8640a73174"


def resolve_transformer(model):
    """Use Diffusers' checkpoint resolution before SGLang's sharded loading."""
    source = model["transformer"]
    subfolder = model["transformer_subfolder"] or ""
    _, revision = H3Transformer.load_config(
        source, subfolder=subfolder, return_commit_hash=True
    )
    options = {"subfolder": subfolder, "revision": revision}
    try:
        index = _get_model_file(
            source, weights_name="diffusion_pytorch_model.safetensors.index.json", **options
        )
    except OSError:
        weights = _get_model_file(
            source, weights_name="diffusion_pytorch_model.safetensors", **options
        )
        return str(Path(weights).parent)
    _get_checkpoint_shard_files(source, index, **options)
    return str(Path(index).parent)


def checkpoint_files(path):
    path = Path(path)
    index = path / "diffusion_pytorch_model.safetensors.index.json"
    if index.is_file():
        mapping = json.loads(index.read_text())["weight_map"]
        files = [path / name for name in sorted(set(mapping.values()))]
    else:
        files = [path / "diffusion_pytorch_model.safetensors"]
    if not all(
        file.is_file() and file.parent.resolve() == path.resolve() for file in files
    ):
        raise ValueError(f"Missing or invalid transformer shards in {path}")
    return files


def weight_plan(source, architecture):
    # Shape validation only: no attention runs on this meta model.
    with torch.device("meta"):
        expected = H3Transformer.from_config(
            architecture, attention_backend="sdpa"
        ).state_dict()
    seen, plan = set(), []
    for file in checkpoint_files(source):
        with safe_open(file, framework="pt", device="cpu") as handle:
            keys = list(handle.keys())
            for key in keys:
                if key in seen or key not in expected:
                    raise ValueError(
                        f"Checkpoint mismatch: unexpected/duplicate tensor {key}"
                    )
                if tuple(handle.get_slice(key).get_shape()) != tuple(
                    expected[key].shape
                ):
                    raise ValueError(f"Checkpoint shape mismatch: {key}")
                seen.add(key)
        plan.append((file, keys))
    if missing := set(expected) - seen:
        raise ValueError(f"Checkpoint mismatch: missing tensors {sorted(missing)[:5]}")
    return plan


def validate_weights(source, architecture):
    return [file for file, _ in weight_plan(source, architecture)]


def checkpoint_weights(plan):
    for file, keys in plan:
        with safe_open(file, framework="pt", device="cpu") as handle:
            for key in keys:
                yield key, handle.get_tensor(key)


def upstream_loader():
    try:
        from sglang.multimodal_gen.runtime.loader.fsdp_load import maybe_load_fsdp_model
        from sglang.multimodal_gen.runtime.loader.weight_load_plan import WeightLoadPlan
    except ImportError as error:
        raise RuntimeError(
            f"SGLang runtime import failed ({SGLANG_COMMIT}); see README.md"
        ) from error
    return maybe_load_fsdp_model, WeightLoadPlan


def load_transformer(config, device, world_size):
    maybe_load_fsdp_model, WeightLoadPlan = upstream_loader()
    model_config = config["model"]
    source = Path(model_config["transformer"])
    architecture = H3Transformer.load_config(source)
    plan = weight_plan(source, architecture)
    init_params, _, _ = H3Transformer.extract_init_dict(architecture)
    init_params["attention_backend"] = config["runtime"]["attention"]
    model = maybe_load_fsdp_model(
        model_cls=H3Transformer,
        init_params=init_params,
        weight_dir_list=[str(file) for file, _ in plan],
        device=device,
        hsdp_replicate_dim=1,
        hsdp_shard_dim=world_size,
        param_dtype=getattr(torch, config["runtime"]["dtype"]),
        reduce_dtype=torch.float32,
        fsdp_inference=True,
        strict=True,
        weight_load_plan=WeightLoadPlan(checkpoint_load_device=torch.device("cpu")),
        weights_iterator=checkpoint_weights(plan),
    )
    return model
