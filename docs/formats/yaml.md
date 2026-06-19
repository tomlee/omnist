# YAML

YAML support covers the **JSON-compatible core** of YAML — the part people
actually use for config: mappings, sequences, and standard scalars. It uses
PyYAML's safe loader, so no arbitrary Python objects are ever constructed.

Requires `pip install pyyaml`.

```python
from dataspec import read_yaml, write_yaml

read_yaml("name: Ann\ntags: [x, y]\n")
# {'name': 'Ann', 'tags': ['x', 'y']}

print(write_yaml({"name": "Ann", "tags": ["x", "y"]}))
# name: Ann
# tags:
# - x
# - y
```

## What's supported

- Mappings (objects), sequences (arrays), strings, integers, numbers, booleans,
  and `null` — the full Document model.
- Any value at the top level, including a bare sequence or scalar.
- `write_yaml` takes `sort_keys` (default off, so insertion order is kept).
- Dates and datetimes round-trip natively (PyYAML reads and writes them as
  timestamps).

## Limitations

dataspec restricts YAML to its tree-shaped, JSON-compatible core. These YAML
features are rejected on read with a `ParseError`, because they don't map to a
plain Document:

- **Non-string keys** — `1: a` (a mapping keyed by an integer). Document keys are
  strings.
- **Anchors and aliases that form cycles** — YAML can describe a structure that
  refers to itself; a Document is a finite tree.

Other advanced YAML (custom tags like `!!python/...`, etc.) never appears because
the safe loader doesn't produce it.

Standalone **time-of-day** values (`datetime.time`) have no native YAML form, so
on write they're converted to a string and reported as a `temporal.stringified`
warning (`check_yaml(doc)` shows it). Dates and datetimes are unaffected — YAML
writes those natively.

## Round-trip behaviour

Within the core, YAML preserves data and scalar types. Reading JSON, writing
YAML, and reading it back gives the same Document:

```python
import json
from dataspec import read_json, read_yaml, write_yaml

original = '{"a": 1, "b": [true, null, "s"], "c": {"d": 2.5}}'
back = read_yaml(write_yaml(read_json(original)))
back == json.loads(original)        # True
```
