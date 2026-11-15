"""One place that finds every external tool and data folder (macOS).

Lookup order for each item:
  1. an environment variable (e.g. RHUBARB_PATH)
  2. ~/.forge-reels/config.json (written by setup/setup-mac.sh)
  3. the PATH (for executables)
  4. a default under FORGE_REELS_HOME (default: ~/forge-reels)

Use from any script in this folder:
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    import _paths
    exe = _paths.rhubarb()
"""
import json
import os
import pathlib
import shutil
import sys

CONFIG_FILE = pathlib.Path.home() / ".forge-reels" / "config.json"
SKILL = pathlib.Path(__file__).resolve().parent.parent          # <workspace>/.claude/skills/forge-reels


def _config():
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def workspace():
    """The ForgeReels workspace: the cloned repo you work in. FORGE_REELS_WORKSPACE, else the folder that holds
    .claude/skills/forge-reels, else the current folder."""
    v = os.environ.get("FORGE_REELS_WORKSPACE")
    if v:
        return pathlib.Path(v).expanduser()
    if SKILL.parent.name == "skills" and SKILL.parents[1].name == ".claude":
        return SKILL.parents[2]
    return pathlib.Path.cwd()


def reels_dir():
    """<workspace>/reels: one working folder per video."""
    return workspace() / "reels"


def output_dir():
    """<workspace>/output: finished videos, ready to post."""
    p = workspace() / "output"
    p.mkdir(parents=True, exist_ok=True)
    return p


def skill_dir(name):
    """Another skill's folder: the workspace's own .claude/skills first, then ~/.claude/skills."""
    local = workspace() / ".claude" / "skills" / name
    return local if local.exists() else pathlib.Path.home() / ".claude" / "skills" / name


def home():
    """FORGE_REELS_HOME: tools, models, fonts and scratch work live here (default ~/forge-reels)."""
    p = os.environ.get("FORGE_REELS_HOME") or _config().get("home") or str(pathlib.Path.home() / "forge-reels")
    return pathlib.Path(p).expanduser()


def _lookup(env, key, default):
    v = os.environ.get(env) or _config().get(key)
    return pathlib.Path(v).expanduser() if v else default


def npx():
    """`npx`, as a command list element."""
    return "npx"


def python():
    """The interpreter running this script: same venv, same packages."""
    return sys.executable


def rhubarb():
    """Rhubarb Lip Sync executable (https://github.com/DanielSWolf/rhubarb-lip-sync, MIT)."""
    p = _lookup("RHUBARB_PATH", "rhubarb", None)
    if p and p.exists():
        return p
    found = shutil.which("rhubarb")
    if found:
        return pathlib.Path(found)
    # setup scripts unpack the release zip under <home>/tools/rhubarb/<release folder>/
    for c in sorted((home() / "tools" / "rhubarb").glob("**/rhubarb")):
        return c
    return home() / "tools" / "rhubarb" / "rhubarb"


def mediapipe_models():
    """Folder holding the MediaPipe .task models (face_landmarker, pose_landmarker, hand_landmarker)."""
    return _lookup("MEDIAPIPE_MODELS", "mediapipe_models", home() / "tools" / "mediapipe")


def fonts_dir():
    """Fonts copied into projects. Default: the OFL fonts bundled with this skill (Inter, Mukta, Noto Sans
    Devanagari). Point FORGE_REELS_FONTS at a brand's own fonts folder to use those instead."""
    return _lookup("FORGE_REELS_FONTS", "fonts", pathlib.Path(__file__).resolve().parent.parent / "assets" / "fonts")


def work_dir(name="scratch"):
    """Scratch folders (smoke test, temp renders)."""
    p = home() / name
    p.mkdir(parents=True, exist_ok=True)
    return p


def sound_python():
    """Python with librosa/soundfile/scipy (the sound pass). Defaults to this interpreter."""
    return os.environ.get("FORGE_REELS_SOUND_PY") or _config().get("sound_python") or sys.executable


def audio_python():
    """Python of the AUDIO venv (earshot + soxr + torch-cpu) for score.py / beatmix.py: FORGE_REELS_AUDIO_PY, config
    'audio_python', or <home>/tools/earshot/.venv. Falls back to this interpreter."""
    v = os.environ.get("FORGE_REELS_AUDIO_PY") or _config().get("audio_python")
    if v:
        return v
    d = home() / "tools" / "earshot" / ".venv"
    exe = d / "bin" / "python"
    return str(exe) if exe.exists() else sys.executable


def voxcpm_python():
    """Python of the VoxCPM2 / mlx-audio venv (setup/setup-voxcpm.sh): FORGE_REELS_VOXCPM_PY, config 'voxcpm_python',
    or <home>/tools/voxcpm/.venv. Returned even when missing; tts_engines reports how to install it."""
    v = os.environ.get("FORGE_REELS_VOXCPM_PY") or _config().get("voxcpm_python")
    return v or str(home() / "tools" / "voxcpm" / ".venv" / "bin" / "python")


def opuscar_dir():
    """lemo-opuscar reference clone (sampler + sample libraries): LEMO_OPUSCAR_DIR, config 'opuscar', or <home>/tools/lemo-opuscar."""
    return _lookup("LEMO_OPUSCAR_DIR", "opuscar", home() / "tools" / "lemo-opuscar")


if __name__ == "__main__":
    print(json.dumps({"home": str(home()), "rhubarb": str(rhubarb()), "rhubarb_exists": rhubarb().exists(),
                      "mediapipe_models": str(mediapipe_models()), "fonts": str(fonts_dir()), "npx": npx(),
                      "config_file": str(CONFIG_FILE)}, indent=1))
