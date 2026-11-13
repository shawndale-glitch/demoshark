"""From recorded runs to deliverables. Once every language is recorded, the video, the deck and the guide
of every language are built in parallel: they only read the run's files, so they never wait on each other.
"""
from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from . import deck, guide, media


def _video(run: dict) -> list[Path]:
    folder = Path(run["out"])
    cues = [(s["start"], s["start"] + s["voice"], s["say"]) for s in run["steps"]]
    srt, vtt = folder / "walkthrough.srt", folder / "walkthrough.vtt"
    media.subtitles(cues, srt, vtt)
    clips = [(folder / "voice" / f"{s['id']}.wav", s["start"]) for s in run["steps"]]
    mp4 = media.narrated_video(Path(run["recording"]), clips, srt, run["lang"], folder / "walkthrough.mp4")
    return [mp4, srt, vtt]


def _deck(run: dict, spec: str) -> list[Path]:
    return [deck.build(run, spec, Path(run["out"]) / f"{run['spec_id']}-{run['lang']}.pptx")]


def _guide(run: dict, spec: str) -> list[Path]:
    return list(guide.build(run, spec, Path(run["out"])))


def report(run: dict) -> Path:
    folder = Path(run["out"])
    rows = "\n".join(f"| {s['id']} | {s['status']} | {s['start']:.2f} | {s['say']} | {s['error']} |" for s in run["steps"])
    checks = "\n".join(f"| {v['fixture']}.{v['field']} | {v.get('equals', 'filled')} | {v.get('got')} | {v['status']} |"
                       for v in run["verify"]) or "| (none) | | | |"
    text = (f"# QA report: {run['spec_id']} ({run['lang']})\n\n"
            f"- Result: **{'PASS' if run['passed'] else 'FAIL'}**\n- Started: {run['started']}\n"
            f"- Voice: {run['engine']}\n- Length: {run['seconds']} s\n\n"
            f"| Step | Status | Starts at (s) | Narration | Error |\n|---|---|---|---|---|\n{rows}\n\n"
            f"| Data check | Expected | Got | Status |\n|---|---|---|---|\n{checks}\n")
    p = folder / "qa-report.md"
    p.write_text(text, encoding="utf-8")
    return p


def outputs(runs: list[dict], spec_path: str, wanted: list[str], workers: int = 6) -> dict[str, list[Path]]:
    """Build every wanted output of every passed run, in parallel. Returns {"<lang>/<output>": [files]}."""
    jobs = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for run in runs:
            report(run)
            if not run["passed"]:
                continue
            if "video" in wanted:
                jobs[pool.submit(_video, run)] = f"{run['lang']}/video"
            if "deck" in wanted:
                jobs[pool.submit(_deck, run, spec_path)] = f"{run['lang']}/deck"
            if "guide" in wanted:
                jobs[pool.submit(_guide, run, spec_path)] = f"{run['lang']}/guide"
        done = {}
        for fut in as_completed(jobs):
            done[jobs[fut]] = fut.result()
            print(f"  built {jobs[fut]:<10} {', '.join(p.name for p in done[jobs[fut]])}", flush=True)
    return done


def load_run(folder: Path) -> dict:
    return json.loads((folder / "run.json").read_text(encoding="utf-8"))
