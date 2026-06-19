# Inferring schemas

`infer` drafts a schema from example Documents. It's the fastest way to get a
starting schema for data you already have — read some real samples, infer, then
tidy the result by hand.

```python
from dataspec import infer

schema = infer([
    {"id": 1, "email": "a@x.io", "roles": ["admin"]},
    {"id": 2, "roles": []},
])
print(schema.to_dsl())
# root { id: integer, email?: string, roles: [string] }
```

`infer(samples)` takes any iterable of Documents and returns a `Schema`. It
needs at least one sample.

## What it does

The guiding principle is **soundness**: an inferred schema always accepts every
sample it was built from. From there it generalizes cautiously.

- **Object fields** are required if they appear in *every* sample, otherwise
  optional. (`email` above is optional because the second sample omits it.)
- **Scalars** union the kinds seen. Mixing integers and floats widens to
  `number`; mixing unlike scalars gives a union like `integer | string`.
- **Nullability** is added when any sample had `null` in that position.
- **Arrays** generalize their items and accept **any length**. Inference never
  locks in the exact lengths it happened to observe — seeing `[1, 2]` doesn't
  mean "always two." If only empty arrays were seen, the array is inferred as
  empty-only (no element type was observed).

```python
infer([{"v": 1}, {"v": "x"}]).to_dsl()      # root { v: integer | string }
infer([{"v": 1}, {"v": 2.5}]).to_dsl()      # root { v: number }
infer([{"v": "a"}, {"v": None}]).to_dsl()   # root { v: string? }
```

## Options

`infer(samples, open_objects=True)` infers **open** objects (extra keys allowed)
instead of closed ones. Use it when your samples don't show every possible key
and you don't want validation to reject unseen fields.

## Limits

- Inference can't read your intent, only your data. It won't invent enums, length
  bounds, `date` types (dates look like strings), or maps. Treat the output as a
  draft and refine it — see the [schema language](schema.md).
- A position that mixes an object with an array, or a structure with a scalar,
  can't be expressed as one type and raises `SchemaError` (dataspec has no
  structural unions).

```python
infer([{"v": 1}, {"v": {"x": 1}}])          # SchemaError: mix of structure and scalar
```

## A typical workflow

```python
from dataspec import read_json, infer

samples = [read_json(line) for line in open("events.jsonl")]
draft = infer(samples)
print(draft.to_dsl())        # copy this into a .schema file and tighten it up
```
