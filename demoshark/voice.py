"""Narration: one audio clip per step, made before the run so the browser can wait exactly as long as the voice.

Engines:
  edge   Microsoft neural voices through the edge-tts package (any OS, 100+ languages, needs internet).
         Only the narration lines are sent to the service: no screenshots and no test data.
  sapi   The voices installed in Windows (offline). Few languages: usually English and the OS language.
  none   Silent. Each step lasts as long as it would take to read its caption.
  auto   edge, else sapi, else none, chosen per language.

Presets pick a voice per language plus a delivery (rate, pitch). `smooth` is the default: the newer
"multilingual" neural voices, a touch slower and lower for a warm, relaxed narration.
Listen before choosing:  demoshark voices --sample --lang en
"""
from __future__ import annotations

import asyncio
import json
import subprocess
import sys
import wave
from pathlib import Path

from . import media

PRESETS: dict[str, dict] = {
    "smooth": {  # warm, relaxed female narrator (default)
        "rate": "-6%", "pitch": "-2Hz",
        "voices": {"en": "en-US-AvaMultilingualNeural", "es": "es-ES-XimenaNeural", "th": "th-TH-PremwadeeNeural",
                   "fr": "fr-FR-VivienneMultilingualNeural", "de": "de-DE-SeraphinaMultilingualNeural",
                   "pt": "pt-BR-ThalitaMultilingualNeural", "it": "it-IT-ElsaNeural", "ja": "ja-JP-NanamiNeural",
                   "zh": "zh-CN-XiaoxiaoNeural", "nl": "nl-NL-ColetteNeural", "vi": "vi-VN-HoaiMyNeural"},
    },
    "warm-male": {  # deep, confident male narrator
        "rate": "-4%", "pitch": "-3Hz",
        "voices": {"en": "en-US-AndrewMultilingualNeural", "es": "es-ES-AlvaroNeural", "th": "th-TH-NiwatNeural",
                   "fr": "fr-FR-RemyMultilingualNeural", "de": "de-DE-FlorianMultilingualNeural",
                   "it": "it-IT-GiuseppeMultilingualNeural", "ja": "ja-JP-KeitaNeural", "zh": "zh-CN-YunxiNeural"},
    },
    "bright": {  # clear and upbeat, for quick tips
        "rate": "+0%", "pitch": "+0Hz",
        "voices": {"en": "en-US-EmmaMultilingualNeural", "es": "es-MX-DaliaNeural", "th": "th-TH-PremwadeeNeural"},
    },
}
SAPI_CULTURE = {"en": "en-US", "es": "es-ES", "fr": "fr-FR", "de": "de-DE", "it": "it-IT", "pt": "pt-PT"}
READING_CPS = 15  # characters per second for silent captions


def settings(cfg: dict, lang: str) -> tuple[str, str, str]:
    """(voice, rate, pitch) for a language: the spec's own voice wins, then the preset."""
    p = PRESETS.get(cfg.get("preset", "smooth"), PRESETS["smooth"])
    base = lang.split("-")[0]
    v = (cfg.get("voices") or {}).get(lang) or p["voices"].get(base) or PRESETS["smooth"]["voices"].get(base, "")
    return v, cfg.get("rate", p["rate"]), cfg.get("pitch", p["pitch"])


def seconds(wav: Path) -> float:
    with wave.open(str(wav)) as w:
        return w.getnframes() / float(w.getframerate())


def _silence(path: Path, secs: float) -> None:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(22050)
        w.writeframes(b"\0\0" * int(22050 * secs))


def _edge(clips: list[tuple[str, Path]], voice: str, rate: str, pitch: str) -> None:
    import edge_tts
    if not voice:
        raise RuntimeError("no neural voice configured for this language")

    async def go():
        for text, wav in clips:
            mp3 = wav.with_suffix(".mp3")
            await edge_tts.Communicate(text, voice, rate=rate, pitch=pitch).save(str(mp3))
            media.ffmpeg(["-i", str(mp3), "-ar", "24000", "-ac", "1", str(wav)])
            mp3.unlink()
    asyncio.run(go())


def _sapi(clips: list[tuple[str, Path]], culture: str) -> None:
    if sys.platform != "win32":
        raise RuntimeError("SAPI voices are Windows only")
    job = Path(clips[0][1]).parent / "_sapi.json"
    job.write_text(json.dumps([{"text": t, "path": str(p)} for t, p in clips]), encoding="utf-8")
    ps = (
        "Add-Type -AssemblyName System.Speech;"
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer;"
        f"$v = $s.GetInstalledVoices() | ? {{ $_.VoiceInfo.Culture.Name -eq '{culture}' }} | select -First 1;"
        f"if (-not $v) {{ throw 'no {culture} voice installed' }};"
        "$s.SelectVoice($v.VoiceInfo.Name);"
        f"foreach ($c in (Get-Content -Raw -Encoding UTF8 '{job}' | ConvertFrom-Json)) {{"
        "  $s.SetOutputToWaveFile($c.path); $s.Speak($c.text) }; $s.Dispose()"
    )
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True)
    job.unlink(missing_ok=True)
    if r.returncode:
        raise RuntimeError(r.stderr.strip().splitlines()[-1] if r.stderr.strip() else "SAPI failed")


def speak(clips: list[tuple[str, Path]], lang: str, engine: str = "auto", cfg: dict | None = None) -> tuple[str, dict[Path, float]]:
    """Write one WAV per (text, path). Returns the engine actually used and each clip's length in seconds."""
    order = ["edge", "sapi", "none"] if engine == "auto" else [engine]
    v, rate, pitch = settings(cfg or {}, lang)
    errors = []
    for eng in order:
        try:
            if eng == "edge":
                _edge(clips, v, rate, pitch)
                eng = f"edge:{v}"
            elif eng == "sapi":
                _sapi(clips, SAPI_CULTURE.get(lang.split("-")[0], lang))
            else:
                for text, wav in clips:
                    _silence(wav, max(1.5, len(text) / READING_CPS))
            return eng, {wav: seconds(wav) for _, wav in clips}
        except Exception as e:  # noqa: BLE001 - try the next engine
            errors.append(f"{eng}: {e}")
            if engine != "auto":
                raise
    raise RuntimeError(f"no voice engine worked for {lang}: {'; '.join(errors)}")


def samples(lang: str, text: str, out: Path) -> list[Path]:
    """One short clip per preset, so the voice can be chosen by ear."""
    out.mkdir(parents=True, exist_ok=True)
    made = []
    for name, p in PRESETS.items():
        v = p["voices"].get(lang.split("-")[0])
        if v:
            wav = out / f"{lang}-{name}.wav"
            _edge([(text, wav)], v, p["rate"], p["pitch"])
            made.append(wav)
    return made


def available() -> dict[str, str]:
    """What each engine can do on this machine (for `demoshark voices`)."""
    out = {}
    try:
        import edge_tts  # noqa: F401
        out["edge"] = "installed (needs internet). Presets: " + "; ".join(
            f"{n} = {p['voices'].get('en')} ({p['rate']}, {p['pitch']})" for n, p in PRESETS.items())
    except ImportError:
        out["edge"] = "not installed: pip install edge-tts"
    if sys.platform == "win32":
        r = subprocess.run(["powershell", "-NoProfile", "-Command",
                            "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer)"
                            ".GetInstalledVoices() | % { $_.VoiceInfo.Culture.Name + ' ' + $_.VoiceInfo.Name }"],
                           capture_output=True, text=True)
        out["sapi"] = ", ".join(x.strip() for x in r.stdout.splitlines() if x.strip()) or "no voices"
    else:
        out["sapi"] = "Windows only"
    out["none"] = "always available (captions only)"
    return out
