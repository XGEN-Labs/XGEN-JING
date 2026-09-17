#!/usr/bin/env bash
set -euo pipefail
ulimit -c 0
DEMO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$DEMO_ROOT"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0,1,2,3,4,5}"
export PYTHONDONTWRITEBYTECODE=1
cuda_libraries="$("${PYTHON:-python3}" -c 'from pathlib import Path; import nvidia; print(":".join(str(p) for root in nvidia.__path__ for p in Path(root).glob("*/lib")))')"
export LD_LIBRARY_PATH="$cuda_libraries${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
"${PYTHON:-python3}" -m torch.distributed.run --standalone --nproc_per_node="${NPROC_PER_NODE:-4}" \
  "$DEMO_ROOT/demo_bidirection.py" "$@"
