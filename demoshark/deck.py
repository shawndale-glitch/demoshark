"""The walk-through as a PowerPoint deck: a title slide, an overview, one slide per step (the ringed
screenshot, the narration, what you should see, the second in the video) and a verification slide.
The narration goes into the speaker notes, so a trainer can present the deck live.
"""
from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

from .i18n import LANG_NAMES, L, mmss

NAVY, TEAL, CORAL, INK, GREY, MIST, WHITE = "0B3954", "087E8B", "FF6B57", "1B2A33", "5B6B75", "EEF4F7", "FFFFFF"
FONT = "Segoe UI"


def _rgb(h: str) -> RGBColor:
    return RGBColor.from_string(h)


def _box(slide, x, y, w, h, fill=None, line=None, shape=MSO_SHAPE.RECTANGLE):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    s.shadow.inherit = False
    if fill:
        s.fill.solid(); s.fill.fore_color.rgb = _rgb(fill)
    else:
        s.fill.background()
    if line:
        s.line.color.rgb = _rgb(line); s.line.width = Pt(0.75)
    else:
        s.line.fill.background()
    return s


def _text(slide, x, y, w, h, text, size=14, color=INK, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, caps=False):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    lines = text if isinstance(text, list) else [text]
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(6)
        r = p.add_run()
        r.text = line.upper() if caps else line
        f = r.font
        f.size, f.bold, f.name = Pt(size), bold, FONT
        f.color.rgb = _rgb(color)
    return tb


def _footer(slide, run, i=None):
    _box(slide, 0, 7.18, 13.333, 0.32, fill=MIST)
    left = f"{run['title']} · {run['spec_id']}" + (f" · {run['steps'][i]['id']}" if i is not None else "")
    _text(slide, 0.5, 7.22, 8, 0.25, left, size=9, color=GREY)
    _text(slide, 8.8, 7.22, 4.03, 0.25, "DEMOShark", size=9, color=TEAL, bold=True, align=PP_ALIGN.RIGHT)


def build(run: dict, spec_path: str, out: Path) -> Path:
    lang, steps, folder = run["lang"], run["steps"], Path(run["out"])
    n, passed = len(steps), sum(s["status"] == "pass" for s in steps)
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    blank = prs.slide_layouts[6]
    prs.core_properties.title = run["title"]
    prs.core_properties.author = "DEMOShark"

    # 1. title
    s = prs.slides.add_slide(blank)
    _box(s, 0, 0, 13.333, 7.5, fill=NAVY)
    _box(s, 0.8, 1.55, 0.9, 0.08, fill=CORAL)
    _text(s, 0.8, 0.8, 6, 0.4, "DEMOShark", size=16, color=CORAL, bold=True)
    _text(s, 0.8, 1.9, 11.5, 1.6, run["title"], size=44, color=WHITE, bold=True)
    _text(s, 0.8, 3.45, 10.5, 1.3, run["summary"], size=20, color="CFE3EC")
    chips = [f"{L(lang, 'app')}: {run['app']}", f"{L(lang, 'lang')}: {LANG_NAMES.get(lang, lang)}",
             f"{L(lang, 'version')} {run['version']}", f"{L(lang, 'date')} {run['started'][:10]}",
             L(lang, "passed", p=passed, n=n)]
    x = 0.8
    for c in chips:
        w = 0.25 + 0.105 * len(c)
        b = _box(s, x, 5.6, w, 0.46, fill="16506F", shape=MSO_SHAPE.ROUNDED_RECTANGLE)
        _text(s, x, 5.6, w, 0.46, c, size=12, color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        x += w + 0.18
    s.notes_slide.notes_text_frame.text = run["summary"]

    # 2. at a glance
    s = prs.slides.add_slide(blank)
    _text(s, 0.6, 0.45, 12, 0.6, L(lang, "glance"), size=30, color=NAVY, bold=True)
    _box(s, 0.6, 1.15, 0.7, 0.06, fill=CORAL)
    rows = min(n, 12)
    h = min(0.62, 5.6 / max(rows, 1))
    for i, st in enumerate(steps[:12]):
        y = 1.5 + i * h
        c = _box(s, 0.6, y + 0.04, 0.42, 0.42, fill=TEAL, shape=MSO_SHAPE.OVAL)
        _text(s, 0.6, y + 0.04, 0.42, 0.42, str(i + 1), size=13, color=WHITE, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        _text(s, 1.25, y + 0.07, 11.2, 0.45, st["say"], size=17, color=INK)
    _footer(s, run)

    # 3. one slide per step
    for i, st in enumerate(steps):
        s = prs.slides.add_slide(blank)
        _text(s, 0.6, 0.38, 6, 0.3, L(lang, "step", i=i + 1, n=n), size=13, color=CORAL, bold=True, caps=True)
        _text(s, 0.6, 0.72, 12.1, 0.9, st["say"], size=26, color=NAVY, bold=True)
        shot = folder / st["shot"] if st.get("shot") else None
        if shot and shot.exists():
            _box(s, 0.58, 1.78, 8.44, 4.79, line="C9D6DD")
            s.shapes.add_picture(str(shot), Inches(0.6), Inches(1.8), Inches(8.4), Inches(4.725))
        px = 9.35
        _box(s, px, 1.8, 3.4, 4.725, fill=MIST)
        _text(s, px + 0.3, 2.05, 2.8, 0.3, L(lang, "see"), size=11, color=TEAL, bold=True, caps=True)
        _text(s, px + 0.3, 2.4, 2.8, 2.2, st.get("result") or st["say"], size=17, color=INK)
        _text(s, px + 0.3, 4.95, 2.8, 0.3, L(lang, "video"), size=11, color=TEAL, bold=True, caps=True)
        _text(s, px + 0.3, 5.25, 2.8, 0.5, mmss(st["start"]), size=24, color=NAVY, bold=True)
        ok = st["status"] == "pass"
        b = _box(s, px + 0.3, 5.95, 1.3, 0.36, fill="1F7A4D" if ok else "B3261E", shape=MSO_SHAPE.ROUNDED_RECTANGLE)
        _text(s, px + 0.3, 5.95, 1.3, 0.36, L(lang, "pass" if ok else "fail"), size=11, color=WHITE, bold=True,
              align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, caps=True)
        s.notes_slide.notes_text_frame.text = st["say"] + ("\n\n" + st["result"] if st.get("result") else "")
        _footer(s, run, i)

    # 4. verification
    s = prs.slides.add_slide(blank)
    _text(s, 0.6, 0.45, 12, 0.6, L(lang, "verified"), size=30, color=NAVY, bold=True)
    _box(s, 0.6, 1.15, 0.7, 0.06, fill=CORAL)
    data = [(st["id"], st["say"], L(lang, "pass" if st["status"] == "pass" else "fail"), mmss(st["start"])) for st in steps]
    data += [(L(lang, "check"), f"{v['fixture']}.{v['field']} = {v.get('got')}", L(lang, v["status"]), "") for v in run["verify"]]
    tbl = s.shapes.add_table(len(data) + 1, 4, Inches(0.6), Inches(1.5), Inches(12.1), Inches(0.4) * (len(data) + 1)).table
    for j, (head, w) in enumerate(zip([L(lang, "steps"), "", L(lang, "result"), L(lang, "video")], [1.6, 7.7, 1.4, 1.4])):
        tbl.columns[j].width = Inches(w)
        tbl.cell(0, j).text = head
    for r, row in enumerate(data, 1):
        for j, v in enumerate(row):
            tbl.cell(r, j).text = v
    for r in range(len(data) + 1):
        for j in range(4):
            cell = tbl.cell(r, j)
            cell.fill.solid(); cell.fill.fore_color.rgb = _rgb(NAVY if r == 0 else (WHITE if r % 2 else MIST))
            for p in cell.text_frame.paragraphs:
                for rn in p.runs:
                    rn.font.size, rn.font.name = Pt(12), FONT
                    rn.font.bold = r == 0
                    rn.font.color.rgb = _rgb(WHITE if r == 0 else INK)
    _text(s, 0.6, 6.6, 12, 0.3, L(lang, "source", spec=spec_path), size=11, color=GREY)
    _footer(s, run)

    prs.save(str(out))
    return out
