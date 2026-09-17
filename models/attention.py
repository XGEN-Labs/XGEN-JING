# Attention projection and rotary conventions follow the Apache-2.0 Diffusers
# MiniMax-H3 implementation (Copyright 2026 The MiniMax and HuggingFace Teams).
"""FA4 attention with global media and slice-local text visibility."""

import torch
from diffusers.models.transformers.transformer_minimax_h3 import _apply_rotary_emb
from torch.nn import functional as F

from runtime.sequence_parallel import gather_sequence, layout


def build_attention_groups(owners, is_media):
    """Precompute local Q and global K/V indices for each visible text group."""
    offset, size, _ = layout(len(owners))
    local_owners = owners[offset:offset + size]
    groups = []
    for owner in local_owners.unique().tolist():
        queries = (local_owners == owner).nonzero().flatten()
        keys = (is_media | (owners == owner)).nonzero().flatten()
        groups.append((queries, keys))
    return groups


def attention(q, k, v, backend):
    if backend == "fa4":
        from flash_attn.cute import flash_attn_func

        out, _ = flash_attn_func(q, k, v, causal=False)
        return out
    return F.scaled_dot_product_attention(
        q.transpose(1, 2), k.transpose(1, 2), v.transpose(1, 2)
    ).transpose(1, 2)


class AttentionProcessor:
    def __init__(self, backend):
        self.backend = backend

    def __call__(self, attn, hidden_states, rotary_emb=None, attention_mask=None):
        q, k, v = [
            layer(hidden_states).unflatten(-1, (attn.heads, -1))
            for layer in (attn.to_q, attn.to_k, attn.to_v)
        ]
        q, k = attn.norm_q(q), attn.norm_k(k)
        if rotary_emb is not None:
            q, k = _apply_rotary_emb(q, *rotary_emb), _apply_rotary_emb(k, *rotary_emb)
        if attention_mask is None:
            out = attention(q, k, v, self.backend)
        else:
            k, v = gather_sequence(k), gather_sequence(v)
            out = torch.zeros_like(q)
            for queries, keys in attention_mask:
                part = attention(
                    q.index_select(1, queries),
                    k.index_select(1, keys),
                    v.index_select(1, keys),
                    self.backend,
                )
                out.index_copy_(1, queries, part)
        return attn.to_out[1](attn.to_out[0](out.flatten(2).to(q.dtype)))
