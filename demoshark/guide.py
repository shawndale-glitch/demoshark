"""The walk-through as a written guide: Markdown (for a repository or wiki) and one HTML page with the video."""
from __future__ import annotations

import html
from pathlib import Path

from .i18n import LANG_NAMES, L, mmss


def build(run: dict, spec_path: str, folder: Path) -> tuple[Path, Path]:
    lang, steps = run["lang"], run["steps"]
    n, passed = len(steps), sum(s["status"] == "pass" for s in steps)
    stamp = f"{L(lang, 'date')} {run['started'][:10]} · {L(lang, 'passed', p=passed, n=n)} · {run['app']} · v{run['version']}"

    md = [f"# {run['title']}", "", run["summary"], "", f"> {stamp}", "",
          f"[{L(lang, 'watch')}](walkthrough.mp4)", ""]
    for i, st in enumerate(steps, 1):
        md += [f"## {i}. {st['say']}", ""]
        if st.get("shot"):
            md += [f"![{st['id']}]({st['shot']})", ""]
        if st.get("result"):
            md += [f"**{L(lang, 'see')}:** {st['result']}", ""]
        md += [f"*{L(lang, 'video')}: {mmss(st['start'])}*", ""]
    md += ["---", "", L(lang, "source", spec=spec_path)]
    md_path = folder / "guide.md"
    md_path.write_text("\n".join(md) + "\n", encoding="utf-8")

    e = html.escape
    items = "".join(
        f'<li><h2>{e(st["say"])}</h2>'
        + (f'<img src="{e(st["shot"])}" alt="{e(st["id"])}" loading="lazy">' if st.get("shot") else "")
        + (f'<p><b>{e(L(lang, "see"))}:</b> {e(st["result"])}</p>' if st.get("result") else "")
        + f'<p class="t"><a href="#" data-t="{st["start"]}">{e(L(lang, "video"))} {mmss(st["start"])}</a></p></li>'
        for st in steps)
    page = f"""<!doctype html><html lang="{lang}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(run['title'])}</title>
<style>
:root{{--navy:#0B3954;--teal:#087E8B;--coral:#FF6B57;--ink:#1B2A33;--grey:#5B6B75;--mist:#EEF4F7}}
body{{margin:0;font:17px/1.55 "Segoe UI","Leelawadee UI","Noto Sans Thai",Roboto,Arial,sans-serif;color:var(--ink);background:#fff}}
header{{background:var(--navy);color:#fff;padding:28px 24px}} header .b{{color:var(--coral);font-weight:700;letter-spacing:.04em}}
main{{max-width:980px;margin:0 auto;padding:24px}} h1{{margin:6px 0 8px;font-size:32px}} header p{{margin:0;color:#cfe3ec}}
.stamp{{display:inline-block;margin-top:14px;background:#16506f;border-radius:20px;padding:4px 14px;font-size:14px}}
video{{width:100%;border-radius:8px;background:#000}} ol{{padding-left:22px}} li{{margin:28px 0}}
h2{{font-size:21px;color:var(--navy);margin:0 0 10px}} img{{width:100%;border:1px solid #c9d6dd;border-radius:6px}}
.t a{{color:var(--teal);font-weight:600;text-decoration:none}} footer{{color:var(--grey);font-size:13px;padding:24px;text-align:center}}
</style></head><body>
<header><div class="b">DEMOShark · {e(LANG_NAMES.get(lang, lang))}</div><h1>{e(run['title'])}</h1><p>{e(run['summary'])}</p>
<span class="stamp">{e(stamp)}</span></header>
<main><video id="v" controls preload="metadata" src="walkthrough.mp4"><track kind="subtitles" src="walkthrough.vtt" srclang="{lang}" default></video>
<ol>{items}</ol></main>
<footer>{e(L(lang, 'source', spec=spec_path))}</footer>
<script>document.querySelectorAll('[data-t]').forEach(a=>a.onclick=e=>{{e.preventDefault();const v=document.getElementById('v');
v.currentTime=+a.dataset.t;v.play();window.scrollTo({{top:0,behavior:'smooth'}})}});</script>
</body></html>"""
    html_path = folder / "guide.html"
    html_path.write_text(page, encoding="utf-8")
    return md_path, html_path
