# TOML

TOML is designed for configuration files. It has first-class dates and is
strict about structure: the top level is always a table (an object). Reading
uses the standard-library `tomllib` (Python 3.11+); writing needs
`pip install tomli_w`.

```python
from dataspec import read_toml, write_toml

read_toml('name = "Ann"\n[address]\ncity = "HK"\n')
# {'name': 'Ann', 'address': {'city': 'HK'}}

print(write_toml({"name": "Ann", "tags": ["x", "y"]}))
# name = "Ann"
# tags = ["x", "y"]
```

## What's supported

- Objects (tables), arrays, strings, integers, numbers, and booleans.
- **Native date types.** `date`, `time`, and `datetime` values round-trip as
  real temporal values, not strings — TOML's standout feature.

```python
import datetime, tomllib
out = write_toml({"created": datetime.datetime(2024, 1, 1, 12, 0)})
tomllib.loads(out)["created"]       # datetime.datetime(2024, 1, 1, 12, 0)
```

## Limitations

- **No `null`.** TOML has no null value. dataspec applies the standard rule:
  a `null` object field is **omitted**; a `null` array item or a top-level
  `null` raises `WriteError`. Use `write_toml(doc, strict=True)` to also reject
  omitted fields.

  ```python
  import tomllib
  from dataspec import write_toml
  tomllib.loads(write_toml({"a": 1, "b": None}))   # {'a': 1}  -- b dropped
  write_toml({"xs": [1, None, 2]})                 # WriteError
  ```

- **The top level must be an object.** A bare array or scalar can't be written:

  ```python
  write_toml([1, 2, 3])               # WriteError: TOML needs a top-level object
  ```

- **Comments aren't preserved.** TOML allows comments, but they aren't part of
  the data model.

## Round-trip behaviour

For any Document that TOML can represent, data and types are preserved exactly,
including dates. The only lossy case is `null` fields, which is why writing one
is reported (or, by default, dropped) rather than guessed at.
