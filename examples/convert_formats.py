#!/usr/bin/env python3
"""Convert one document between all four formats, and show the adjustment report.

Run: python3 examples/convert_formats.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from dataspec import (
    read_json, write_yaml, write_toml, write_xml, check_toml,
    WriteError, WriteReport,
)


def main():
    doc = read_json('{"name": "Ann", "age": 30, "tags": ["x", "y"], '
                    '"address": {"city": "HK"}}')

    print("-- YAML --");  print(write_yaml(doc), end="")
    print("-- TOML --");  print(write_toml(doc))
    print("-- XML  --");  print(write_xml(doc, root="person"))

    print("\n-- lenient by default --")
    # TOML has no null: the null field is dropped, the null array item too.
    rep = WriteReport()
    out = write_toml({"a": 1, "b": None, "xs": [1, None, 2]}, report=rep)
    print("output:\n" + out.rstrip())
    print("adjustments:")
    for adj in rep:
        print(f"  [{adj.severity}] {adj.path}: {adj.message}")

    print("\n-- inspect before writing (check_*) --")
    rep = check_toml({"xs": [1, None, 2]})
    print("safe to write losslessly?", bool(rep))   # False: an error-level drop

    print("\n-- strict: refuse anything lossy --")
    try:
        write_toml({"xs": [1, None, 2]}, strict=True)
    except WriteError as e:
        print("WriteError:", e)


if __name__ == "__main__":
    main()
