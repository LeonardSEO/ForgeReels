"""Speech recognition (what was said) and forced alignment (when each script word was said), in one place.

    asr.transcribe(wav, engine="faster-whisper", model="small", language="nl") -> [{text, start, end}, ...]
    asr.transcribe_many(wavs, engine="parakeet", language="nl")                 -> one list per wav, model loaded once
    asr.align(wav, asr.script_words(line), "nl")                               -> one item per SCRIPT word

Engines for transcribe:
  faster-whisper  the main venv; CPU int8. Default model small (small.en for English).
  parakeet        NVIDIA Parakeet TDT 0.6B v3 through mlx-audio in the VoxCPM venv (setup/setup-voxcpm.sh), Apple
                  Silicon; 25 European languages incl. Dutch. On the M4 it was ~2.7x faster than Whisper small with a
                  lower error rate (gate 2, 2026-11-15).
Both put the first word of a clip at 0.0 when the clip starts with silence, which is why word TIMES come from
align(): CTC forced alignment of the SCRIPT text (torchaudio forced_align, BSD) with an Apache 2.0 wav2vec2 model
per language (ALIGN_MODELS). torchaudio's MMS_FA aligned as well but its weights are CC BY-NC: never for client work.
"""
import json
import pathlib
import re
import subprocess
import sys
import unicodedata

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import _paths  # noqa: E402

ENGINES = ("faster-whisper", "parakeet")
PARAKEET = "mlx-community/parakeet-tdt-0.6b-v3"


def load16k(path):
    """16 kHz mono float32 via ffmpeg. faster-whisper 1.2.1 decodes files with PyAV and passes
    metadata_errors=, which the installed PyAV 19 rejects (TypeError); handing it an array skips PyAV."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


_WM = {}


def _whisper(wav, model, language):
    from faster_whisper import WhisperModel
    if model not in _WM:
        _WM[model] = WhisperModel(model, device="cpu", compute_type="int8")
    # no initial_prompt: feeding the script back in makes Whisper repeat it (fake words past the audio)
    segs, _ = _WM[model].transcribe(load16k(wav), language=language, word_timestamps=True,
                                    condition_on_previous_text=False, beam_size=5)
    return [{"text": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)}
            for s in segs for w in s.words if w.word.strip()]


def merge_tokens(tokens):
    """Parakeet subword tokens [(text, start, end)] -> words; a token starting with a space opens a new word."""
    words, new = [], True
    for text, start, end in tokens:
        if not text.strip():
            new = True
            continue
        if new or text.startswith(" "):
            words.append({"text": text.strip(), "start": round(start, 3), "end": round(end, 3)})
        else:
            words[-1]["text"] += text
            words[-1]["end"] = round(end, 3)
        new = False
    return words


def _parakeet(wavs, language):
    py = _paths.voxcpm_python()
    if not pathlib.Path(py).exists():
        raise SystemExit("ASR engine 'parakeet' is not installed. Install it with:\n  sh setup/setup-voxcpm.sh")
    code = ("import json,sys\nfrom mlx_audio.stt.utils import load\nm=load(sys.argv[1])\nout=[]\n"
            "for w in json.loads(sys.stdin.read()):\n r=m.generate(w)\n"
            " out.append([(t.text,t.start,t.end) for s in r.sentences for t in s.tokens])\nprint(json.dumps(out))\n")
    r = subprocess.run([py, "-I", "-c", code, PARAKEET], input=json.dumps([str(w) for w in wavs]),
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"parakeet failed: {r.stderr[-800:]}")
    return [merge_tokens(t) for t in json.loads(r.stdout.strip().splitlines()[-1])]


def transcribe_many(wavs, engine="faster-whisper", model=None, language=None):
    if engine == "parakeet":
        return _parakeet(wavs, language)
    if engine != "faster-whisper":
        raise SystemExit(f"unknown ASR engine '{engine}'; choose one of {', '.join(ENGINES)}")
    model = model or ("small.en" if language == "en" else "small")
    return [_whisper(w, model, language) for w in wavs]


def transcribe(wav, engine="faster-whisper", model=None, language=None):
    return transcribe_many([wav], engine, model, language)[0]


def language_for(explicit, starts):
    """Language for ASR/alignment: --language, else starts.json "lang" (written by build_vo.py), else English.
    espeak names are cut to their ISO code (en-us -> en)."""
    return (explicit or starts.get("lang") or "en").split("-")[0]


def script_words(text):
    """Words as the captions show them (punctuation attached)."""
    return text.split()


def align_key(word):
    """What MMS can align: lower-case a-z and apostrophes, diacritics folded (één -> een). Digits drop out."""
    return re.sub(r"[^a-z']", "", unicodedata.normalize("NFKD", word.lower()))


def fill_guesses(items, dur):
    """Words with no time (nothing alignable, e.g. "30.000") get the gap between their timed neighbours,
    split evenly, and "guessed": true."""
    out = [dict(x) for x in items]
    i = 0
    while i < len(out):
        if out[i]["start"] is not None:
            i += 1
            continue
        j = i
        while j < len(out) and out[j]["start"] is None:
            j += 1
        lo = out[i - 1]["end"] if i > 0 else 0.0
        hi = out[j]["start"] if j < len(out) else dur
        step = (hi - lo) / (j - i)
        for k in range(i, j):
            out[k].update(start=round(lo + (k - i) * step, 3), end=round(lo + (k - i + 1) * step, 3), guessed=True)
        i = j
    return out


# Apache 2.0 CTC models (MMS_FA would be CC BY-NC 4.0: not for client work). ~1.2 GB each, downloaded once.
ALIGN_MODELS = {"en": "jonatasgrosman/wav2vec2-large-xlsr-53-english",
                "nl": "jonatasgrosman/wav2vec2-large-xlsr-53-dutch"}
_AL = {}


def _char_ids(word, vocab):
    ids = []
    for c in word.lower():
        c = c if c in vocab else align_key(c)
        if c in vocab:
            ids.append(vocab[c])
    return ids


def align(wav, words, lang):
    """Forced-align script words to a clip (CTC forced alignment, torchaudio). One item per word, clip seconds."""
    import soundfile as sf
    import torch
    import torchaudio.functional as F
    from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
    name = ALIGN_MODELS.get((lang or "en").split("-")[0])
    if name is None:
        raise SystemExit(f"no aligner for language '{lang}'; add an Apache/MIT CTC model to asr.ALIGN_MODELS")
    if name not in _AL:
        _AL[name] = (Wav2Vec2ForCTC.from_pretrained(name).eval(), Wav2Vec2Processor.from_pretrained(name))
    model, proc = _AL[name]
    vocab = proc.tokenizer.get_vocab()
    blank = proc.tokenizer.pad_token_id
    y, sr = sf.read(str(wav), dtype="float32")
    y = torch.from_numpy(y.mean(1) if y.ndim > 1 else y)[None]
    dur = y.shape[1] / sr
    y = F.resample(y, sr, 16000)
    keys = [_char_ids(w, vocab) for w in words]
    flat = [t for k in keys for t in k]
    items = [{"text": w, "start": None, "end": None} for w in words]
    if flat:
        x = proc(y[0].numpy(), sampling_rate=16000, return_tensors="pt").input_values
        with torch.inference_mode():
            em = model(x).logits
        al, scores = F.forced_align(em.log_softmax(-1), torch.tensor([flat], dtype=torch.int32), blank=blank)
        spans = F.merge_tokens(al[0], scores[0].exp(), blank=blank)
        sec = y.shape[1] / em.shape[1] / 16000
        k = 0
        for item, ks in zip(items, keys):
            if ks:
                item["start"] = round(spans[k].start * sec, 3)
                item["end"] = round(spans[k + len(ks) - 1].end * sec, 3)
                k += len(ks)
    return fill_guesses(items, dur)
