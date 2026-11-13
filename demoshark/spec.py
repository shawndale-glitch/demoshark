"""Load a walk-through spec, resolve its texts for one language, and check it against the rules DS1-DS10.

The spec is the single source: every caption, voice line, slide, guide step and QA check comes from it.
A spec that fails a rule with severity "error" is never run.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

SCHEMA = Path(__file__).parent / "schema" / "walkthrough.schema.json"
SAFE_ENVIRONMENTS = {"test", "training", "demo"}
PLACEHOLDER = re.compile(r"\{\{\s*(\w+)\.(\w+)\s*\}\}")
RULES = {
    "DS1": "The spec matches the schema (demoshark/schema/walkthrough.schema.json)",
    "DS2": "Every title, summary, step line, result and visible name is given in every declared language",
    "DS3": "The environment is test, training or demo, and the base URL doesn't point at production",
    "DS4": "Controls are found the way a person finds them: role + visible name, label, placeholder or text",
    "DS5": "Every step after the first one has an expected result (expect) that the run checks",
    "DS6": "Test data is fictional: no e-mail addresses, phone or document numbers; people and companies are Demo/Test",
    "DS7": "Step ids are unique and numbered in order: S1, S2, S3...",
    "DS8": "Every {{fixture.field}} placeholder names a declared fixture",
    "DS9": "Every step has a result line for the guide and the deck (warning)",
    "DS10": "The walk-through is short enough to follow: at most 12 steps (warning)",
}


@dataclass
class Finding:
    rule: str
    severity: str  # error | warning
    where: str
    message: str

    def __str__(self) -> str:
        return f"{self.rule} [{self.severity}] {self.where}: {self.message}"


@dataclass
class Spec:
    path: Path
    data: dict

    @property
    def id(self) -> str:
        return self.data["walkthrough"]["id"]

    @property
    def languages(self) -> list[str]:
        return self.data["walkthrough"]["languages"]

    @property
    def steps(self) -> list[dict]:
        return self.data["steps"]

    @property
    def outputs(self) -> list[str]:
        return self.data.get("outputs", ["video", "deck", "guide"])

    def text(self, value: Any, lang: str, data: dict | None = None) -> str:
        """A text field in `lang`, with {{fixture.field}} placeholders filled from `data`."""
        if value is None:
            return ""
        s = value if isinstance(value, str) else value.get(lang) or next(iter(value.values()))
        if data:
            s = PLACEHOLDER.sub(lambda m: str(data.get(m[1], {}).get(m[2], m[0])), s)
        return s

    def meta(self, key: str, lang: str) -> str:
        return self.text(self.data["walkthrough"].get(key), lang)


def load(path: str | Path) -> Spec:
    p = Path(path)
    return Spec(p, yaml.safe_load(p.read_text(encoding="utf-8")))


# ------------------------------------------------------------------ rules
def _texts(node: Any, where: str):
    """Yield (where, value) for every multilingual text field in a spec."""
    if isinstance(node, dict):
        for k, v in node.items():
            w = f"{where}.{k}" if where else k
            if k in ("title", "summary", "say", "result", "name", "label", "placeholder", "text", "value"):
                yield w, v
            if isinstance(v, (dict, list)):
                yield from _texts(v, w)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _texts(v, f"{where}[{i}]")


def check(spec: Spec) -> list[Finding]:
    f: list[Finding] = []
    d = spec.data

    # DS1 schema
    try:
        import jsonschema
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        for e in sorted(jsonschema.Draft202012Validator(schema).iter_errors(d), key=lambda e: list(e.path)):
            f.append(Finding("DS1", "error", "/".join(map(str, e.path)) or "(root)", e.message))
    except ImportError:  # pragma: no cover
        f.append(Finding("DS1", "warning", "(root)", "jsonschema is not installed; schema not checked"))
    if any(x.rule == "DS1" and x.severity == "error" for x in f):
        return f  # the other rules assume the structure is right

    langs = spec.languages
    # DS2 every language present
    for where, v in _texts({k: d[k] for k in ("walkthrough", "steps") if k in d}, ""):
        if isinstance(v, dict):
            missing = [lg for lg in langs if lg not in v]
            if missing:
                f.append(Finding("DS2", "error", where, f"missing {', '.join(missing)}"))
            if any("TODO" in str(x) for x in v.values()):
                f.append(Finding("DS2", "error", where, "contains TODO"))

    # DS3 environment
    env = d["walkthrough"]["environment"]
    if env not in SAFE_ENVIRONMENTS:
        f.append(Finding("DS3", "error", "walkthrough.environment", f"'{env}' is not one of {sorted(SAFE_ENVIRONMENTS)}"))
    if re.search(r"(^|[.\-/])prod(uction)?([.\-/:]|$)", d["app"]["base_url"], re.I):
        f.append(Finding("DS3", "error", "app.base_url", "looks like a production address"))

    # DS4 is enforced by the schema (no css/xpath/selector keys); also reject selector-looking names
    for where, v in _texts(d.get("steps", []), "steps"):
        for s in ([v] if isinstance(v, str) else v.values() if isinstance(v, dict) else []):
            if where.endswith((".name", ".label")) and re.match(r"^[#.\[/]|^//", str(s)):
                f.append(Finding("DS4", "error", where, f"'{s}' looks like a CSS/XPath selector, not a visible name"))

    # DS5 expect on every step after the first
    for i, st in enumerate(spec.steps):
        if i > 0 and "expect" not in st and st["do"]["action"] != "wait":
            f.append(Finding("DS5", "error", st["id"], "no expect: the run could not prove this step worked"))

    # DS6 fictional data
    email = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
    phone = re.compile(r"\+?\d[\d\s().-]{7,}\d")
    for name, fx in (d.get("fixtures") or {}).items():
        for k, v in fx.items():
            sv = str(v)
            if email.search(sv) or (phone.search(sv) and not re.fullmatch(r"[\d.]+", sv)):
                f.append(Finding("DS6", "error", f"fixtures.{name}.{k}", "looks like a real e-mail or phone number"))
            if k in ("name", "supplier", "customer", "person", "company", "surname") and not re.match(r"^(Demo|Test)\b", sv):
                f.append(Finding("DS6", "error", f"fixtures.{name}.{k}", f"'{sv}' must start with Demo or Test"))

    # DS7 step ids
    ids = [st["id"] for st in spec.steps]
    if ids != [f"S{i}" for i in range(1, len(ids) + 1)]:
        f.append(Finding("DS7", "error", "steps", f"ids are {ids}; expected S1..S{len(ids)} in order"))

    # DS8 placeholders
    declared = set((d.get("fixtures") or {}).keys())
    for where, v in _texts(d.get("steps", []), "steps"):
        for s in ([v] if isinstance(v, str) else v.values() if isinstance(v, dict) else []):
            for m in PLACEHOLDER.finditer(str(s)):
                if m[1] not in declared:
                    f.append(Finding("DS8", "error", where, f"{{{{{m[1]}.{m[2]}}}}} names an undeclared fixture"))
    for v in d.get("verify", []):
        if v["fixture"] not in declared:
            f.append(Finding("DS8", "error", "verify", f"fixture '{v['fixture']}' is not declared"))

    # DS9 result lines (warning)
    for st in spec.steps:
        if "result" not in st:
            f.append(Finding("DS9", "warning", st["id"], "no result line; the guide and deck will only show the narration"))

    # DS10 length (warning)
    if len(spec.steps) > 12:
        f.append(Finding("DS10", "warning", "steps", f"{len(spec.steps)} steps; split it into shorter walk-throughs"))
    return f
