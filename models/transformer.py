# Forward conventions adapted from the Apache-2.0 Diffusers MiniMax-H3 model.
# Copyright 2026 The MiniMax and HuggingFace Teams. All rights reserved.
"""Public H3 modules with independent text refinement and camera FiLM."""

import inspect
from typing import ClassVar

import torch
from diffusers import MiniMaxH3Transformer3DModel
from diffusers.configuration_utils import register_to_config
from diffusers.models.transformers.transformer_minimax_h3 import (
    MINIMAX_H3_MODALITY_NUM,
    MiniMaxH3RotaryPosEmbed,
    MiniMaxH3TransformerBlock,
)
from torch import nn
from torch.nn import functional as F
from runtime.sequence_parallel import gather_sequence, layout

from .attention import AttentionProcessor
from .control import Control


class ControlledBlock(MiniMaxH3TransformerBlock):
    def forward(
        self,
        hidden,
        temb,
        indices,
        rotary,
        mask,
        encoded=None,
        control_indices=None,
        injector=None,
    ):
        shifts = [value.index_select(0, indices) for value in self.adaln_proj(temb)]
        shift_a, scale_a, gate_a, shift_f, scale_f, gate_f = shifts
        hidden = hidden + gate_a * self.attn(
            self.norm1(hidden) * (1 + scale_a) + shift_a, rotary, mask
        )
        conditioned = (
            hidden if encoded is None else injector(hidden, encoded, control_indices)
        )
        # Camera FiLM modifies the FFN input; the attention residual is preserved.
        return hidden + gate_f * self.ff(
            self.norm2(conditioned) * (1 + scale_f) + shift_f
        )


class H3Transformer(MiniMaxH3Transformer3DModel):
    # SGLang's public-source loader contract; no custom sharding implementation.
    _fsdp_forward_methods = ()
    _fsdp_mixed_dtype_params = True
    param_names_mapping: ClassVar[dict] = {}
    _fsdp_shard_conditions: ClassVar[list] = [
        lambda name, module: isinstance(module, ControlledBlock)
    ]

    @register_to_config
    def __init__(
        self,
        num_attention_heads=56,
        attention_head_dim=128,
        hidden_size=5376,
        num_layers=50,
        num_refiner_layers=2,
        ffn_dim=14336,
        in_channels=24,
        audio_in_channels=32,
        patch_size=(1, 2, 2),
        text_dim=5120,
        freq_dim=256,
        time_embed_hidden_dim=5376,
        time_embed_dim=2688,
        rope_freq_dim=16,
        rope_theta=10000.0,
        norm_eps=1e-5,
        qk_norm_eps=1e-5,
        final_norm_eps=1e-5,
        control_config=None,
        attention_backend="fa4",
    ):
        values = locals()
        fields = inspect.signature(MiniMaxH3Transformer3DModel.__init__).parameters
        architecture = {key: values[key] for key in fields if key != "self"}
        super().__init__(**architecture)
        self.architecture = dict(self.config)
        block_fields = inspect.signature(MiniMaxH3TransformerBlock.__init__).parameters
        block_args = {
            key: self.architecture[key] for key in block_fields if key != "self"
        }
        self.transformer_blocks = nn.ModuleList(
            [ControlledBlock(**block_args) for _ in range(self.config.num_layers)]
        )
        self.control_config = control_config or {"enable": False}
        self.control = (
            Control(self.control_config, self.architecture)
            if self.control_config["enable"]
            else None
        )
        self.attention_backend = attention_backend
        for block in self.transformer_blocks:
            block.attn.set_processor(AttentionProcessor(attention_backend))
        for block in self.token_refiner.refiner_blocks:
            block.attn.set_processor(AttentionProcessor(attention_backend))
        # Preserve the original projection dtypes during upstream sharded loading.
        for name in self._keep_in_fp32_modules:
            self.get_submodule(name).float()

    def post_load_weights(self):
        # RoPE is computed state, absent from the checkpoint.
        device = next(self.parameters()).device
        rope = MiniMaxH3RotaryPosEmbed(
            rope_freq_dim=self.config.rope_freq_dim, rope_theta=self.config.rope_theta
        )
        self.rope.inv_freq = rope.inv_freq.to(device)

    def forward(self, packed, timestep, timestep_indices, mask):
        video = self.proj_in(packed.video.to(self.proj_in.weight.dtype))
        audio = self.audio_proj_in(packed.audio.to(self.audio_proj_in.weight.dtype))
        texts = self.context_embedder(
            packed.text.to(self.context_embedder.weight.dtype)
        )
        text = torch.cat(
            [
                self.token_refiner(part)
                for part in texts.split(packed.text_lengths, dim=1)
            ],
            dim=1,
        )
        hidden = text.new_zeros(1, len(packed.token_tags), text.shape[-1])
        for indices, values in (
            (packed.text_indices, text),
            (packed.video_indices, video),
            (packed.audio_indices, audio),
        ):
            hidden = hidden.index_copy(1, indices, values.to(hidden.dtype))
        offset, local_length, world = layout(hidden.shape[1])
        padding = local_length * world - hidden.shape[1]
        hidden = F.pad(hidden, (0, 0, 0, padding))[:, offset:offset + local_length].contiguous()
        position_ids = F.pad(packed.position_ids, (0, 0, 0, padding))[offset:offset + local_length]
        rotary = self.rope(position_ids)
        temb = self.time_embedder(
            self.time_proj(timestep).to(self.time_embedder.linear_1.weight.dtype)
        )
        indices = timestep_indices * MINIMAX_H3_MODALITY_NUM + packed.token_tags
        indices = F.pad(indices, (0, padding))[offset:offset + local_length]
        encoded, control_indices = (
            (None, None) if self.control is None else self.control(packed.controls)
        )
        if control_indices is not None:
            selected = (control_indices >= offset) & (control_indices < offset + local_length)
            encoded, control_indices = encoded[selected], control_indices[selected] - offset
        for index, block in enumerate(self.transformer_blocks):
            hidden = block(
                hidden,
                temb,
                indices,
                rotary,
                mask,
                encoded,
                control_indices,
                None if self.control is None else self.control.block_injectors[index],
            )
        local_timesteps = F.pad(timestep_indices, (0, padding))[offset:offset + local_length]
        hidden = self.norm_out(hidden, temb, local_timesteps)
        return (
            gather_sequence(self.proj_out(hidden.to(self.proj_out.weight.dtype))).index_select(
                1, packed.video_indices
            ),
            gather_sequence(self.audio_proj_out(
                hidden.to(self.audio_proj_out.weight.dtype)
            )).index_select(1, packed.audio_indices),
        )
