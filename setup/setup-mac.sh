#!/usr/bin/env bash
# ForgeReels setup for macOS (Apple Silicon recommended; Intel works without the MLX extras).
#
#   bash setup/setup-mac.sh            # full setup
#   bash setup/setup-mac.sh --no-skills   # skip installing the third-party skills
#   bash setup/setup-mac.sh --minimal     # only the skills marked "# core" in setup/skills.txt
#
# What it does (nothing outside these places is touched):
#   1. ffmpeg, Node, Python via Homebrew (only if missing)
#   2. a Python venv at $FORGE_REELS_HOME/venv with setup/requirements.txt
#   3. Rhubarb Lip Sync + MediaPipe models into $FORGE_REELS_HOME/tools
#   4. copies the skill to ~/.claude/skills/forge-reels (an existing copy is moved to ~/.claude/skills-archive first)
#   5. installs the third-party skills listed in setup/skills.txt with `npx skills add`
#   6. writes ~/.forge-reels/config.json and runs the smoke test
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$HERE")"
HOME_DIR="${FORGE_REELS_HOME:-$HOME/forge-reels}"
[ "$(uname -s)" = "Darwin" ] || { echo "ForgeReels runs on macOS only."; exit 1; }
NO_SKILLS=0; MINIMAL=0
for arg in "$@"; do
  case "$arg" in --no-skills) NO_SKILLS=1 ;; --minimal) MINIMAL=1 ;; *) echo "unknown option: $arg"; exit 1 ;; esac
done
say() { printf '\n==> %s\n' "$*"; }

say "1/6 Tools (ffmpeg, node, python)"
command -v brew >/dev/null || { echo "Homebrew is needed: https://brew.sh"; exit 1; }
command -v ffmpeg >/dev/null || brew install ffmpeg
command -v node   >/dev/null || brew install node
command -v python3.12 >/dev/null || brew install python@3.12
for t in ffmpeg ffprobe node npx; do command -v "$t" >/dev/null || { echo "missing: $t"; exit 1; }; done
PY="$(command -v python3.12 || command -v python3)"
echo "python: $PY ($("$PY" --version))"

say "2/6 Python venv + packages ($HOME_DIR/venv)"
mkdir -p "$HOME_DIR/tools" "$HOME_DIR/assets"
[ -x "$HOME_DIR/venv/bin/python" ] || "$PY" -m venv "$HOME_DIR/venv"
VPY="$HOME_DIR/venv/bin/python"
"$VPY" -m pip install --upgrade pip >/dev/null
# requirements.lock = the versions tested on a Mac M4 (pip freeze); requirements.txt when there is no lock
REQ="$HERE/requirements.txt"; [ "$(uname -m)" = "arm64" ] && [ -s "$HERE/requirements.lock" ] && REQ="$HERE/requirements.lock"
"$VPY" -m pip install -r "$REQ"

say "3/6 Rhubarb Lip Sync + MediaPipe models"
RB="$HOME_DIR/tools/rhubarb"
if ! ls "$RB"/*/rhubarb >/dev/null 2>&1; then
  mkdir -p "$RB"
  curl -fL -o "$RB/rhubarb.zip" "https://github.com/DanielSWolf/rhubarb-lip-sync/releases/download/v1.14.0/Rhubarb-Lip-Sync-1.14.0-macOS.zip"
  (cd "$RB" && unzip -q rhubarb.zip && rm rhubarb.zip)
  xattr -dr com.apple.quarantine "$RB" 2>/dev/null || true
fi
RHUBARB="$(ls "$RB"/*/rhubarb | head -1)"; chmod +x "$RHUBARB"
MP="$HOME_DIR/tools/mediapipe"; mkdir -p "$MP"
base=https://storage.googleapis.com/mediapipe-models
[ -s "$MP/face_landmarker.task" ]       || curl -fL -o "$MP/face_landmarker.task"       "$base/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
[ -s "$MP/pose_landmarker_heavy.task" ] || curl -fL -o "$MP/pose_landmarker_heavy.task" "$base/pose_landmarker/pose_landmarker_heavy/float16/1/pose_landmarker_heavy.task"
[ -s "$MP/hand_landmarker.task" ]       || curl -fL -o "$MP/hand_landmarker.task"       "$base/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"

say "4/6 Workspace: the skill is already here (.claude/skills/forge-reels); Claude Code loads it in this folder"
mkdir -p "$ROOT/reels" "$ROOT/output" "$ROOT/brand" "$ROOT/references"

if [ "$NO_SKILLS" = 0 ]; then
  say "5/6 Third-party skills (setup/skills.txt$([ "$MINIMAL" = 1 ] && echo ', core only'))"
  grep -v '^#' "$HERE/skills.txt" | grep '|' | { [ "$MINIMAL" = 1 ] && grep '# core' || cat; } | while IFS='|' read -r repo skill; do
    repo="$(echo "$repo" | xargs)"; skill="$(echo "${skill%%#*}" | xargs)"
    echo "  $repo -> $skill"
    (cd "$ROOT" && npx --yes skills add "$repo" --skill "$skill" -y -a claude-code </dev/null) >/dev/null || echo "  (failed: install it later by hand)"
  done
fi

say "6/6 Config + smoke test"
# merge, so paths written by setup-voxcpm.sh / setup-audio.sh survive a re-run
"$VPY" -I - "$HOME_DIR" "$RHUBARB" "$MP" "$VPY" <<'PY'
import json, pathlib, sys
f = pathlib.Path.home() / ".forge-reels" / "config.json"; f.parent.mkdir(exist_ok=True)
c = json.loads(f.read_text()) if f.exists() else {}
c.update(home=sys.argv[1], rhubarb=sys.argv[2], mediapipe_models=sys.argv[3], sound_python=sys.argv[4])
f.write_text(json.dumps(c, indent=1)); print("config:", f)
PY
export HYPERFRAMES_PYTHON="$VPY"
"$VPY" -I "$ROOT/.claude/skills/forge-reels/scripts/smoke_test.py" || { echo "Smoke test failed: read the output above."; exit 1; }

cat <<EOF

Done. Two things to remember:
  - Run the skill's Python scripts with:  $VPY -I <script>
  - Kokoro TTS needs:  export HYPERFRAMES_PYTHON="$VPY"   (add it to ~/.zshrc to make it permanent)
Optional: add the Playwright MCP, video-analyzer and mcp-video servers in Claude Code (see references/toolchain.md).
EOF
