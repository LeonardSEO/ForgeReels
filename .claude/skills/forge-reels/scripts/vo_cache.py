"""Content-keyed cache for generated voice lines and transcripts.

A file is reused only when its sidecar `<file>.key` holds the key of everything that made it (engine, model,
voice, speed, language, text; or for a transcript: the audio bytes and the ASR settings). A file without a
sidecar is stale, so files made before this cache existed are regenerated once.

    k = vo_cache.key(engine="kokoro", voice="af_heart", text="Hello")
    if not vo_cache.fresh(wav, k): make(wav); vo_cache.stamp(wav, k)
"""
import hashlib
import json
import pathlib


def key(**parts):
    return hashlib.sha256(json.dumps(parts, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def file_hash(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def _sidecar(path):
    path = pathlib.Path(path)
    return path.with_name(path.name + ".key")


def fresh(path, k):
    s = _sidecar(path)
    return pathlib.Path(path).exists() and s.exists() and s.read_text(encoding="utf-8").strip() == k


def stamp(path, k):
    _sidecar(path).write_text(k, encoding="utf-8")
