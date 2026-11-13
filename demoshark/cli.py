"""DEMOShark command line.

  demoshark check SPEC                 check a spec against the rules (nothing runs)
  demoshark run SPEC [options]         record it in each language, then build video + deck + guide in parallel
  demoshark build SPEC                 rebuild the outputs from the last recording, without running the app
  demoshark demo [--drift]             start the bundled Paydesk app and run the sample spec end to end
  demoshark app [--drift]              start the bundled Paydesk app on its own
  demoshark voices [--sample]          show the voice engines, or write sample clips of each preset
"""
from __future__ import annotations

import argparse
import socket
import sys
import threading
import time
from pathlib import Path

import os

from . import __version__, build, spec as specmod

SAMPLE_SPEC = Path(__file__).resolve().parent.parent / "specs" / "paydesk-approve-invoice.yaml"


def _utf8() -> None:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass


def cmd_check(a) -> int:
    sp = specmod.load(a.spec)
    findings = specmod.check(sp)
    errors = [f for f in findings if f.severity == "error"]
    for f in findings:
        print(f)
    print(f"{'FAIL' if errors else 'PASS'}  {a.spec}: {len(errors)} errors, {len(findings) - len(errors)} warnings")
    return 1 if errors else 0


def _record_and_build(sp, langs, a, base_url=None) -> int:
    from . import runner
    findings = specmod.check(sp)
    errors = [f for f in findings if f.severity == "error"]
    if errors:
        for f in errors:
            print(f)
        print("The spec has errors: nothing was run.")
        return 2
    out = Path(a.out)
    runs, t0 = [], time.monotonic()
    for lang in langs:
        print(f"> recording {sp.id} [{lang}] ...", flush=True)
        r = runner.record(sp, lang, out, engine=a.voice, headed=a.headed, base_url=base_url,
                          captions=getattr(a, "captions", "burn") != "none")
        failed = next((s for s in r.steps if s.status == "fail"), None)
        status = "PASS" if r.passed else (f"FAIL at {failed.id}: {failed.error}" if failed else "FAIL in the data check")
        print(f"  {status}  {sum(s.status == 'pass' for s in r.steps)}/{len(r.steps)} steps, {r.seconds} s, voice {r.engine}")
        runs.append(build.load_run(Path(r.out)))
    wanted = [o for o in sp.outputs if o in (a.only.split(",") if a.only else sp.outputs)]
    print(f"> building {', '.join(wanted)} for {len([r for r in runs if r['passed']])} language(s) in parallel ...", flush=True)
    build.outputs(runs, _shown(sp.path), wanted)
    ok = all(r["passed"] for r in runs)
    print(f"{'PASS' if ok else 'FAIL'}  {sp.id}  {', '.join(langs)}  in {time.monotonic() - t0:.0f} s  ->  {out / sp.id}")
    if not ok:
        print("Nothing is published for a language that failed: its qa-report.md says where and why.")
    return 0 if ok else 1


def _shown(p: Path) -> str:
    """The spec path as shown in the outputs: relative, so no local folder names leak into a deck or guide."""
    try:
        return Path(os.path.relpath(p)).as_posix()
    except ValueError:
        return p.name


def _langs(sp, a) -> list[str]:
    return a.lang.split(",") if a.lang else sp.languages


def cmd_run(a) -> int:
    sp = specmod.load(a.spec)
    return _record_and_build(sp, _langs(sp, a), a, a.base_url)


def cmd_build(a) -> int:
    sp = specmod.load(a.spec)
    runs = [build.load_run(Path(a.out) / sp.id / lg) for lg in _langs(sp, a) if (Path(a.out) / sp.id / lg / "run.json").exists()]
    if not runs:
        print("No recording found: run `demoshark run` first.")
        return 2
    build.outputs(runs, _shown(sp.path), sp.outputs)
    return 0


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def cmd_demo(a) -> int:
    from .demoapp import paydesk
    port = _free_port()
    srv = paydesk.serve(port, a.drift)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    print(f"Paydesk {'(drift: Approve renamed) ' if a.drift else ''}on http://127.0.0.1:{port}")
    try:
        sp = specmod.load(a.spec or SAMPLE_SPEC)
        return _record_and_build(sp, _langs(sp, a), a, f"http://127.0.0.1:{port}")
    finally:
        srv.shutdown()


def cmd_app(a) -> int:
    from .demoapp import paydesk
    srv = paydesk.serve(a.port, a.drift)
    print(f"Paydesk on http://127.0.0.1:{a.port}/?lang=en  (es, th also)  Ctrl+C to stop")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


def cmd_voices(a) -> int:
    from . import voice
    if a.sample:
        text = a.text or {"en": "Select Approve. The Approve invoice window opens.",
                          "es": "Pulse Aprobar. Se abre la ventana Aprobar factura.",
                          "th": "กดอนุมัติ หน้าต่างอนุมัติใบแจ้งหนี้จะเปิดขึ้น"}.get(a.lang, "This is how I sound.")
        for p in voice.samples(a.lang, text, Path(a.out) / "voice-samples"):
            print(f"  wrote {p}")
        return 0
    for k, v in voice.available().items():
        print(f"{k:5} {v}")
    return 0


def main(argv: list[str] | None = None) -> int:
    _utf8()
    ap = argparse.ArgumentParser(prog="demoshark", description="Spec in, narrated video + deck + guide out.")
    ap.add_argument("--version", action="version", version=f"DEMOShark {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def run_opts(p, spec_required=True):
        if spec_required:
            p.add_argument("spec")
        p.add_argument("--lang", help="comma-separated languages (default: all in the spec)")
        p.add_argument("--voice", default="spec", choices=["spec", "auto", "edge", "sapi", "none"],
                       help="voice engine (default: what the spec says)")
        p.add_argument("--headed", action="store_true", help="show the browser while recording")
        p.add_argument("--captions", default="burn", choices=["burn", "none"],
                       help="none: leave the caption bar out of the recording (for tools that add their own)")
        p.add_argument("--out", default="build", help="output folder (default: build)")
        p.add_argument("--only", help="build only some outputs: video,deck,guide")

    p = sub.add_parser("check", help="check a spec against the rules"); p.add_argument("spec"); p.set_defaults(f=cmd_check)
    p = sub.add_parser("run", help="record and build"); run_opts(p); p.add_argument("--base-url"); p.set_defaults(f=cmd_run)
    p = sub.add_parser("build", help="rebuild outputs from the last recording"); run_opts(p); p.set_defaults(f=cmd_build)
    p = sub.add_parser("demo", help="run the sample spec against the bundled app"); run_opts(p, False)
    p.add_argument("--spec"); p.add_argument("--drift", action="store_true", help="rename Approve, as a vendor release might")
    p.set_defaults(f=cmd_demo)
    p = sub.add_parser("app", help="start the bundled Paydesk app"); p.add_argument("--port", type=int, default=8765)
    p.add_argument("--drift", action="store_true"); p.set_defaults(f=cmd_app)
    p = sub.add_parser("voices", help="voice engines and samples"); p.add_argument("--sample", action="store_true")
    p.add_argument("--lang", default="en"); p.add_argument("--text"); p.add_argument("--out", default="build")
    p.set_defaults(f=cmd_voices)
    a = ap.parse_args(argv)
    return a.f(a)


if __name__ == "__main__":
    sys.exit(main())
