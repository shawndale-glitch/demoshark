"""Record one language of a walk-through: create test data, drive the app step by step, check each step,
read the data back, delete it. Everything the outputs need is written to build/<id>/<lang>/.

Per step: caption + highlight on screen, the voice plays, the action happens, the expected result is
checked. If any check fails, the run stops there and nothing is published for that language.
"""
from __future__ import annotations

import json
import shutil
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

from . import adapters, voice
from .spec import Spec

STEP_TIMEOUT_MS = 8000
OVERLAY = """
(() => {
  if (window.__ds) return;
  const css = `#__ds_cap{position:fixed;left:50%;bottom:28px;transform:translateX(-50%);max-width:86%;z-index:2147483647;
     background:rgba(11,57,84,.94);color:#fff;font:600 20px/1.4 "Segoe UI","Leelawadee UI","Noto Sans Thai",Arial,sans-serif;
     padding:12px 22px;border-radius:10px;box-shadow:0 6px 20px rgba(0,0,0,.25);pointer-events:none;text-align:center}
   #__ds_cap b{display:inline-block;background:#FF6B57;color:#fff;border-radius:6px;padding:0 8px;margin-right:10px;font-size:15px}
   #__ds_ring{position:fixed;z-index:2147483646;border:4px solid #FF6B57;border-radius:8px;pointer-events:none;
     box-shadow:0 0 0 6px rgba(255,107,87,.25);transition:all .25s ease}`;
  const ready = () => {
    if (document.getElementById('__ds_cap')) return;
    const st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);
    const cap = document.createElement('div'); cap.id = '__ds_cap'; cap.hidden = true; document.body.appendChild(cap);
    const ring = document.createElement('div'); ring.id = '__ds_ring'; ring.hidden = true; document.body.appendChild(ring);
  };
  window.__ds = {
    caption(text, n, total) { ready(); const c = document.getElementById('__ds_cap');
      c.innerHTML = `<b>${n}/${total}</b>`; c.appendChild(document.createTextNode(text)); c.hidden = false; },
    ring(b) { ready(); const r = document.getElementById('__ds_ring');
      Object.assign(r.style, {left:(b.x-8)+'px', top:(b.y-8)+'px', width:(b.width+16)+'px', height:(b.height+16)+'px'}); r.hidden = false; },
    clear() { const r = document.getElementById('__ds_ring'); if (r) r.hidden = true; },
  };
  if (document.readyState !== 'loading') ready(); else document.addEventListener('DOMContentLoaded', ready);
})();
"""


class StepFailed(Exception):
    pass


@dataclass
class StepResult:
    id: str
    say: str
    result: str
    status: str = "not run"
    start: float = 0.0       # seconds into the video
    voice: float = 0.0       # narration length
    shot: str = ""           # screenshot file (relative to the language folder)
    error: str = ""
    box: dict | None = None  # the control's bounding box in viewport pixels {x, y, width, height}


@dataclass
class Run:
    spec_id: str
    lang: str
    title: str
    summary: str
    app: str
    version: str
    engine: str = ""
    passed: bool = False
    started: str = ""
    seconds: float = 0.0
    steps: list[StepResult] = field(default_factory=list)
    verify: list[dict] = field(default_factory=list)
    recording: str = ""
    out: str = ""
    viewport: dict = field(default_factory=dict)   # recording size, so boxes can be mapped onto video frames
    captions: bool = True                          # False: the caption bar was left out of the recording

    def save(self) -> None:
        Path(self.out, "run.json").write_text(json.dumps(asdict(self), ensure_ascii=False, indent=2), encoding="utf-8")


def _locate(page, target: dict, spec: Spec, lang: str, data: dict):
    root = page
    if "within" in target:
        root = _locate(page, target["within"], spec, lang, data).first
    t = lambda k: spec.text(target[k], lang, data)
    if "role" in target:
        return root.get_by_role(target["role"], name=t("name"), exact=True) if "name" in target else root.get_by_role(target["role"])
    if "label" in target:
        return root.get_by_label(t("label"), exact=True)
    if "placeholder" in target:
        return root.get_by_placeholder(t("placeholder"), exact=True)
    return root.get_by_text(t("text"), exact=True)


def _describe(target: dict, spec: Spec, lang: str, data: dict) -> str:
    keys = [k for k in ("role", "name", "label", "placeholder", "text") if k in target]
    return " ".join(f'{k}="{spec.text(target[k], lang, data)}"' if k != "role" else target[k] for k in keys)


def record(spec: Spec, lang: str, out_root: Path, engine: str = "auto", headed: bool = False,
           base_url: str | None = None, captions: bool = True) -> Run:
    from playwright.sync_api import sync_playwright

    d = spec.data
    base = (base_url or d["app"]["base_url"]).rstrip("/")
    out = out_root / spec.id / lang
    if out.exists():
        shutil.rmtree(out)
    (out / "voice").mkdir(parents=True)
    (out / "shots").mkdir()
    run = Run(spec.id, lang, spec.meta("title", lang), spec.meta("summary", lang), d["app"]["name"],
              d["walkthrough"]["version"], started=datetime.now().isoformat(timespec="seconds"), out=str(out),
              captions=captions)

    # 1. test data
    adapter = adapters.get(d["app"].get("adapter"), base)
    data = {k: adapter.create(k, v) for k, v in (d.get("fixtures") or {}).items()}

    try:
        # 2. narration first: the browser waits as long as each line takes to say
        lines = [spec.text(st["say"], lang, data) for st in spec.steps]
        vcfg = d.get("voice", {})
        clips = [(line, out / "voice" / f"{st['id']}.wav") for line, st in zip(lines, spec.steps)]
        run.engine, lens = voice.speak(clips, lang, engine if engine != "spec" else vcfg.get("engine", "auto"), vcfg)
        run.steps = [StepResult(st["id"], line, spec.text(st.get("result"), lang, data), voice=lens[wav])
                     for st, (line, wav) in zip(spec.steps, clips)]

        # 3. the recorded run
        vp = d["app"].get("viewport", {"width": 1280, "height": 720})
        run.viewport = dict(vp)
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=not headed)
            ctx = browser.new_context(viewport=vp, locale=lang, record_video_dir=str(out / "_rec"), record_video_size=vp)
            ctx.add_init_script(OVERLAY)
            page = ctx.new_page()
            t0 = time.monotonic()
            total = len(spec.steps)
            try:
                for i, (st, res) in enumerate(zip(spec.steps, run.steps), 1):
                    _step(page, st, res, i, total, spec, lang, data, base, out, t0, captions)
                    res.status = "pass"
                page.wait_for_timeout(1500)
                run.passed = True
            except StepFailed as e:
                res.status, res.error = "fail", str(e)
                page.screenshot(path=str(out / "shots" / f"{res.id}-fail.png"))
                res.shot = f"shots/{res.id}-fail.png"
            run.seconds = round(time.monotonic() - t0, 2)
            video = page.video
            ctx.close()
            browser.close()
            rec = Path(video.path()) if video else None
            if rec and run.passed:
                run.recording = str(rec.rename(out / "recording.webm"))
            shutil.rmtree(out / "_rec", ignore_errors=True)

        # 4. read the data back
        if run.passed:
            for v in d.get("verify", []):
                got = adapter.get(v["fixture"], data[v["fixture"]]).get(v["field"])
                ok = (got not in (None, "", [])) if v.get("filled") else got == v.get("equals")
                run.verify.append({**v, "got": got, "status": "pass" if ok else "fail"})
            run.passed = all(v["status"] == "pass" for v in run.verify)
    finally:
        for k, rec_ in data.items():
            try:
                adapter.delete(k, rec_)
            except Exception:  # noqa: BLE001 - cleanup is best effort
                pass
    run.save()
    return run


def _step(page, st: dict, res: StepResult, i: int, total: int, spec: Spec, lang: str, data: dict,
          base: str, out: Path, t0: float, captions: bool = True) -> None:
    do = st["do"]
    lp = spec.data["app"].get("lang_param")
    if do["action"] == "open":
        url = base + do.get("path", "/")
        if lp:
            url += ("&" if "?" in url else "?") + f"{lp}={lang}"
        page.goto(url)
        page.wait_for_load_state("networkidle")
    res.start = round(time.monotonic() - t0, 2)
    if captions:
        page.evaluate("([t, n, k]) => window.__ds.caption(t, n, k)", [res.say, i, total])
    loc = None
    if "target" in do:
        loc = _locate(page, do["target"], spec, lang, data).first
        try:
            loc.wait_for(state="visible", timeout=STEP_TIMEOUT_MS)
        except Exception:
            raise StepFailed(f"could not find {_describe(do['target'], spec, lang, data)} on screen "
                             f"within {STEP_TIMEOUT_MS // 1000} s") from None
        box = loc.bounding_box()
        if box:
            res.box = {k: round(box[k], 1) for k in ("x", "y", "width", "height")}
            page.evaluate("b => window.__ds.ring(b)", box)
    # screenshot for the guide and the deck: the control to use, ringed, without the caption bar
    shot = out / "shots" / f"{st['id']}.png"
    if do["action"] != "open":
        page.wait_for_timeout(300)
        page.screenshot(path=str(shot), style="#__ds_cap{visibility:hidden}")
    lead = max(0.6, res.voice * 0.55)
    page.wait_for_timeout(int(lead * 1000))
    value = spec.text(do.get("value"), lang, data)
    if do["action"] == "click":
        loc.click()
    elif do["action"] == "fill":
        loc.fill(value)
    elif do["action"] == "select":
        loc.select_option(label=value)
    elif do["action"] == "press":
        (loc or page.keyboard).press(do["key"])
    elif do["action"] == "wait":
        page.wait_for_timeout(int(do.get("seconds", 1) * 1000))
    page.evaluate("() => window.__ds && window.__ds.clear()")
    rest = res.voice - (time.monotonic() - t0 - res.start) + 0.5
    if rest > 0:
        page.wait_for_timeout(int(rest * 1000))
    exp = st.get("expect")
    if exp:
        eloc = _locate(page, exp["target"], spec, lang, data).first
        try:
            if exp.get("visible") is False:
                eloc.wait_for(state="hidden", timeout=STEP_TIMEOUT_MS)
            else:
                eloc.wait_for(state="visible", timeout=STEP_TIMEOUT_MS)
                if "value" in exp:
                    want = spec.text(exp["value"], lang, data)
                    if eloc.input_value() != want:
                        raise StepFailed(f"{_describe(exp['target'], spec, lang, data)} holds '{eloc.input_value()}', expected '{want}'")
        except StepFailed:
            raise
        except Exception:
            raise StepFailed(f"expected {_describe(exp['target'], spec, lang, data)} "
                             f"{'to close' if exp.get('visible') is False else 'on screen'}, within {STEP_TIMEOUT_MS // 1000} s") from None
    if do["action"] == "open":
        page.screenshot(path=str(shot), style="#__ds_cap{visibility:hidden}")
    res.shot = f"shots/{st['id']}.png"
