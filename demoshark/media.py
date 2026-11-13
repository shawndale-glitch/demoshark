"""ffmpeg helpers: put each narration clip at its step's second in the recording, and write subtitles.

ffmpeg comes with the imageio-ffmpeg package, so there is nothing else to install.
"""
from __future__ import annotations

import subprocess
from pathlib import Path


def exe() -> str:
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def ffmpeg(args: list[str]) -> None:
    r = subprocess.run([exe(), "-hide_banner", "-loglevel", "error", "-y"] + args, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError("ffmpeg failed: " + r.stderr[-1200:])


def stamp(t: float, sep: str = ",") -> str:
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


def subtitles(cues: list[tuple[float, float, str]], srt: Path, vtt: Path) -> None:
    srt.write_text("".join(f"{i}\n{stamp(a)} --> {stamp(b)}\n{t}\n\n" for i, (a, b, t) in enumerate(cues, 1)), encoding="utf-8")
    vtt.write_text("WEBVTT\n\n" + "".join(f"{stamp(a, '.')} --> {stamp(b, '.')}\n{t}\n\n" for a, b, t in cues), encoding="utf-8")


def narrated_video(recording: Path, clips: list[tuple[Path, float]], srt: Path, lang: str, out: Path) -> Path:
    """recording + one WAV per step at its start second -> H.264/AAC MP4 with a subtitle track."""
    args = ["-i", str(recording)]
    for wav, _ in clips:
        args += ["-i", str(wav)]
    args += ["-i", str(srt)]
    n = len(clips)
    parts = [f"[{k + 1}:a]adelay={int(t * 1000)}:all=1,aresample=48000[a{k}]" for k, (_, t) in enumerate(clips)]
    mix = "".join(f"[a{k}]" for k in range(n)) + f"amix=inputs={n}:normalize=0:duration=longest[aud]"
    args += ["-filter_complex", ";".join(parts + [mix]), "-map", "0:v", "-map", "[aud]", "-map", f"{n + 1}:s"]
    args += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p", "-r", "25",
             "-c:a", "aac", "-b:a", "128k", "-c:s", "mov_text", "-metadata:s:s:0", f"language={_iso639_2(lang)}",
             "-movflags", "+faststart", str(out)]
    ffmpeg(args)
    return out


def _iso639_2(lang: str) -> str:
    return {"en": "eng", "es": "spa", "th": "tha", "fr": "fra", "de": "deu", "it": "ita", "pt": "por",
            "nl": "nld", "ja": "jpn", "zh": "zho", "ar": "ara", "vi": "vie"}.get(lang.split("-")[0], "und")
