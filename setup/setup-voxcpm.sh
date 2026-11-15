#!/bin/sh
# Optional, Apple Silicon only: VoxCPM2 premium TTS and Parakeet v3 ASR through mlx-audio (MIT), in their own venv.
#   VoxCPM2 (Apache 2.0 code + weights, 30 languages incl. Dutch), 8-bit MLX weights ~2.5 GB on first use.
#   Parakeet TDT 0.6B v3 (25 European languages incl. Dutch, word timestamps) for scripts/asr.py.
# Usage: sh setup/setup-voxcpm.sh
set -e
[ "$(uname -s)-$(uname -m)" = "Darwin-arm64" ] || { echo "mlx-audio needs an Apple Silicon Mac"; exit 1; }
HOME_DIR="${FORGE_REELS_HOME:-$HOME/forge-reels}"; V="$HOME_DIR/tools/voxcpm/.venv"
PY="$(command -v python3.12 || command -v python3)"
[ -x "$V/bin/python" ] || "$PY" -m venv "$V"
"$V/bin/python" -m pip install -q --upgrade pip
"$V/bin/python" -m pip install -q mlx-audio soundfile
"$PY" - "$V/bin/python" <<'PY'
import json, pathlib, sys
f = pathlib.Path.home() / ".forge-reels" / "config.json"; f.parent.mkdir(exist_ok=True)
c = json.loads(f.read_text()) if f.exists() else {}
c.update(voxcpm_python=sys.argv[1]); f.write_text(json.dumps(c, indent=1)); print("config:", f)
PY
"$V/bin/python" -c "import mlx_audio, mlx.core as mx; print('mlx-audio', getattr(mlx_audio, '__version__', '?'), 'device', mx.default_device())"
