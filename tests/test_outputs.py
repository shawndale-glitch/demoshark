"""The deck, guide and subtitles build from a run record alone (no browser, no network)."""
import json
import struct
import zlib
from pathlib import Path

from pptx import Presentation

from demoshark import build, media


def _png(path: Path, w=64, h=36):
    raw = b"".join(b"\0" + b"\x0b\x39\x54" * w for _ in range(h))
    chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def _run(tmp: Path) -> dict:
    (tmp / "shots").mkdir()
    steps = []
    for i in range(1, 4):
        _png(tmp / "shots" / f"S{i}.png")
        steps.append({"id": f"S{i}", "say": f"Step {i} line.", "result": f"Result {i}.", "status": "pass",
                      "start": i * 3.0, "voice": 2.0, "shot": f"shots/S{i}.png", "error": ""})
    run = {"spec_id": "demo-x", "lang": "es", "title": "Título", "summary": "Resumen.", "app": "Demo", "version": "1.0.0",
           "engine": "none", "passed": True, "started": "2026-11-13T10:00:00", "seconds": 12.0, "steps": steps,
           "verify": [{"fixture": "invoice", "field": "status", "equals": "approved", "got": "approved", "status": "pass"}],
           "recording": "", "out": str(tmp)}
    (tmp / "run.json").write_text(json.dumps(run), encoding="utf-8")
    return run


def test_deck_and_guide(tmp_path):
    run = _run(tmp_path)
    done = build.outputs([run], "specs/demo-x.yaml", ["deck", "guide"])
    deck = Presentation(str(done["es/deck"][0]))
    assert len(deck.slides) == 3 + 3  # title, overview, 3 steps, verification
    assert deck.slides[2].notes_slide.notes_text_frame.text.startswith("Step 1 line.")
    md = (tmp_path / "guide.md").read_text(encoding="utf-8")
    assert "Qué debe ver" in md and "shots/S2.png" in md
    assert (tmp_path / "qa-report.md").exists()


def test_subtitles(tmp_path):
    media.subtitles([(1.5, 3.25, "Hola"), (61.0, 62.0, "Adiós")], tmp_path / "a.srt", tmp_path / "a.vtt")
    assert "00:00:01,500 --> 00:00:03,250" in (tmp_path / "a.srt").read_text(encoding="utf-8")
    assert "00:01:01.000 --> 00:01:02.000" in (tmp_path / "a.vtt").read_text(encoding="utf-8")


def test_failed_run_publishes_nothing(tmp_path):
    run = _run(tmp_path)
    run["passed"] = False
    assert build.outputs([run], "x.yaml", ["deck", "guide", "video"]) == {}
    assert (tmp_path / "qa-report.md").exists()
