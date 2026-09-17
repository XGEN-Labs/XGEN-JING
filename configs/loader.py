"""YAML configuration with optional key=value overrides."""

import sys
from pathlib import Path

from omegaconf import OmegaConf

ROOT = Path(__file__).resolve().parents[1]


def local_path(value):
    path = Path(value).expanduser()
    return str(path.resolve() if path.is_absolute() else (ROOT / path).resolve())


def load_yaml(path, stack=()):
    path = Path(path).resolve()
    if path in stack:
        raise ValueError("Cyclic YAML inheritance")
    if ROOT not in path.parents:
        raise ValueError("YAML files must be inside this demo directory")
    config = OmegaConf.load(path)
    if not OmegaConf.is_dict(config):
        raise ValueError("Expected a YAML mapping")
    parent = config.pop("_base_", None)
    if parent is not None:
        config = OmegaConf.merge(
            load_yaml(path.parent / parent, (*stack, path)), config
        )
    return config


def load_config(arguments=None):
    args = list(sys.argv[1:] if arguments is None else arguments)
    filename = (
        args.pop(0) if args and "=" not in args[0] else "configs/bidirection.yaml"
    )
    if any("=" not in item or item.startswith("--") for item in args):
        raise ValueError(
            "Use: demo_bidirection.py [configs/bidirection.yaml] key=value ..."
        )
    config = load_yaml(local_path(filename))
    OmegaConf.set_struct(config, True)
    config = OmegaConf.to_container(
        OmegaConf.merge(config, OmegaConf.from_dotlist(args)), resolve=True
    )
    config["cases"] = local_path(config["cases"])
    for key in ("h3", "transformer"):
        source = config["model"][key]
        if not isinstance(source, str) or not source.strip():
            raise ValueError(f"model.{key} must be a Hugging Face repository or directory")
        if source.startswith(("/", ".", "~")) or (ROOT / source).is_dir():
            config["model"][key] = local_path(source)
    subfolder = config["model"]["transformer_subfolder"]
    if subfolder is not None and (
        not isinstance(subfolder, str)
        or Path(subfolder).is_absolute()
        or ".." in Path(subfolder).parts
    ):
        raise ValueError("model.transformer_subfolder must be a relative directory or null")
    config["output"]["directory"] = local_path(config["output"]["directory"])
    if config["runtime"]["dtype"] not in ("bfloat16", "float32"):
        raise ValueError("runtime.dtype must be bfloat16 or float32")
    if config["runtime"]["attention"] not in ("fa4", "sdpa"):
        raise ValueError("runtime.attention must be fa4 or sdpa")
    if config["runtime"]["attention"] == "fa4" and config["runtime"]["dtype"] != "bfloat16":
        raise ValueError("FA4 requires runtime.dtype=bfloat16")
    offset = config["runtime"]["dit_device_offset"]
    if type(offset) is not int or offset < 0:
        raise ValueError("runtime.dit_device_offset must be a non-negative integer")
    g = config["generation"]
    for key in ("height", "width", "num_frames"):
        if type(g[key]) is not int or g[key] <= 0:
            raise ValueError(f"generation.{key} must be a positive integer")
    if g["height"] % 32 or g["width"] % 32:
        raise ValueError("height and width must be multiples of 32")
    if g["first_chunk_size"] not in (0, 2):
        raise ValueError("first_chunk_size must be 0 or 2")
    if not 0 <= g["reference_timestep"] <= 1:
        raise ValueError("reference_timestep must lie in [0, 1]")
    if not 0 <= g["ref_image_slots"] <= g["reserved_slots"]:
        raise ValueError("Invalid reference/reserved slot counts")
    return config
