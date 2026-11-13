"""Adapters create the test data a walk-through needs, read it back to verify the result, and delete it.

An adapter is a class with three methods (see docs/ADAPTING.md):

    create(kind, values) -> dict    make one fixture (e.g. an invoice) and return it with its fields
    get(kind, record)    -> dict    read the fixture back after the run
    delete(kind, record) -> None    remove it

`none` is for walk-throughs that need no test data.
"""
from __future__ import annotations

from .paydesk import PaydeskAdapter


class NoAdapter:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def create(self, kind: str, values: dict) -> dict:
        return dict(values)

    def get(self, kind: str, record: dict) -> dict:
        return record

    def delete(self, kind: str, record: dict) -> None:
        pass


ADAPTERS = {"paydesk": PaydeskAdapter, "none": NoAdapter}


def get(name: str | None, base_url: str):
    try:
        return ADAPTERS[name or "none"](base_url)
    except KeyError:
        raise SystemExit(f"unknown adapter '{name}'; known: {', '.join(ADAPTERS)}") from None
