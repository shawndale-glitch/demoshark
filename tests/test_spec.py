"""The rules catch what they should, and the sample spec passes them."""
import copy
from pathlib import Path

import pytest

from demoshark import spec as S

SAMPLE = Path(__file__).resolve().parent.parent / "specs" / "paydesk-approve-invoice.yaml"


@pytest.fixture
def sp():
    return S.load(SAMPLE)


def rules(sp, mutate):
    d = copy.deepcopy(sp.data)
    mutate(d)
    return {f.rule for f in S.check(S.Spec(sp.path, d)) if f.severity == "error"}


def test_sample_spec_passes(sp):
    assert [f for f in S.check(sp) if f.severity == "error"] == []


def test_missing_language_is_ds2(sp):
    assert "DS2" in rules(sp, lambda d: d["steps"][0]["say"].pop("th"))


def test_production_is_ds3(sp):
    assert "DS3" in rules(sp, lambda d: d["walkthrough"].update(environment="production"))
    assert "DS3" in rules(sp, lambda d: d["app"].update(base_url="https://prod.example.com"))


def test_css_selector_is_rejected(sp):
    # the schema has no css/xpath key (DS1), and a selector-looking name is DS4
    assert "DS1" in rules(sp, lambda d: d["steps"][1]["do"]["target"].update(css="#num"))
    assert "DS4" in rules(sp, lambda d: d["steps"][2]["do"]["target"].update(name="#search-btn"))


def test_step_without_expect_is_ds5(sp):
    assert "DS5" in rules(sp, lambda d: d["steps"][3].pop("expect"))


def test_real_looking_data_is_ds6(sp):
    assert "DS6" in rules(sp, lambda d: d["fixtures"]["invoice"].update(supplier="Acme Ltd"))
    assert "DS6" in rules(sp, lambda d: d["fixtures"]["invoice"].update(contact="ana@example.com"))


def test_step_order_is_ds7(sp):
    assert "DS7" in rules(sp, lambda d: d["steps"][1].update(id="S9"))


def test_unknown_placeholder_is_ds8(sp):
    assert "DS8" in rules(sp, lambda d: d["steps"][1]["do"].update(value="{{order.number}}"))


def test_text_resolves_language_and_placeholders(sp):
    st = sp.steps[5]["expect"]["target"]["text"]
    assert sp.text(st, "es", {"invoice": {"number": "INV-1"}}) == "Factura INV-1 aprobada."
    assert sp.text(st, "th", {"invoice": {"number": "INV-1"}}) == "อนุมัติใบแจ้งหนี้ INV-1 แล้ว"
