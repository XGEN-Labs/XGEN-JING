"""Inference sequence sharding over the DiT process group."""

import torch
import torch.distributed as dist


def layout(length):
    world = dist.get_world_size() if dist.is_initialized() else 1
    rank = dist.get_rank() if dist.is_initialized() else 0
    size = (length + world - 1) // world
    return rank * size, size, world


def gather_sequence(value):
    """Gather equal-length [batch, sequence, ...] shards in rank order."""
    world = dist.get_world_size() if dist.is_initialized() else 1
    if world == 1:
        return value
    source = value.transpose(0, 1).contiguous()
    output = torch.empty(
        (source.shape[0] * world, *source.shape[1:]),
        dtype=value.dtype, device=value.device,
    )
    dist.all_gather_into_tensor(output, source)
    return output.transpose(0, 1)
