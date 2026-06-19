# Formats

dataspec treats JSON, YAML, TOML, and XML as four ways to write down the **same**
Document. Each format has:

- a `read_*(text)` function that parses a string into a Document, and
- a `write_*(doc)` function that serializes a Document back to a string.

```python
from dataspec import read_json, write_toml
write_toml(read_json('{"name": "Ann"}'))     # 'name = "Ann"\n'
```

Because they share one model, converting is just *read one, write another*. The
only thing you have to know is what each format can and can't represent.

## The guarantee: lossless, or a clear error

dataspec never silently changes your data to make it fit. If a Document contains
something the target format can't express, the writer raises a `WriteError`
explaining what and where:

```python
from dataspec import write_toml, WriteError
write_toml({"x": None})         # ok: a null *field* is dropped (see below)
write_toml([1, 2, 3])           # WriteError: TOML needs a top-level object
```

The practical consequence: if `write_B(read_A(x))` succeeds, the result holds
the same data, and reading it back gives you the same Document again. If it
can't, you get an error instead of a corrupted file.

## How `null` is handled

JSON and YAML have `null`. TOML and XML don't. dataspec uses one consistent rule
when writing to a format without `null`:

- a `null` **object field** is **omitted** from the output;
- a `null` **array item** or a `null` at the **top level** is a `WriteError`
  (dropping it would change the data).

Pass `strict=True` to `write_toml` / `write_xml` to turn the omitted-field case
into an error too, when you'd rather be told than have fields silently dropped.

## Comparison table

How each format represents the building blocks of a Document.
Legend: ✅ full support · ⚠️ works with a caveat · ❌ not supported.

| Capability | JSON | YAML | TOML | XML |
|---|:---:|:---:|:---:|:---:|
| Object / map | ✅ | ✅ | ✅ | ✅ |
| Array / list | ✅ | ✅ | ✅ | ⚠️ |
| String | ✅ | ✅ | ✅ | ✅ |
| Integer | ✅ | ✅ | ✅ | ⚠️ |
| Number (float) | ✅ | ✅ | ✅ | ⚠️ |
| Boolean | ✅ | ✅ | ✅ | ⚠️ |
| `null` | ✅ | ✅ | ❌ | ❌ |
| Date / time / datetime | ⚠️ | ⚠️ | ✅ | ⚠️ |
| Top-level array | ✅ | ✅ | ❌ | ❌ |
| Top-level scalar | ✅ | ✅ | ❌ | ⚠️ |
| Nested arrays (array of arrays) | ✅ | ✅ | ✅ | ❌ |
| Comments in the format | ❌ | ✅ | ✅ | ✅ |
| Exact scalar type after round-trip | ✅ | ✅ | ✅ | ⚠️ |

Notes on the caveats:

- **XML arrays** are repeated elements and must be a named field; XML has no way
  to write a bare or nested array. **XML scalars** are untyped text, so types are
  recovered on read with best-effort guessing (`"30"` → `30`, `"true"` → `True`),
  which means a numeric-looking string can come back as a number.
- **Dates** have no representation in JSON or XML, so they travel as ISO-8601
  strings; schemas accept those. TOML has native date types. YAML reads/writes
  dates and datetimes natively but not standalone times.
- **Comments** are allowed by three of the formats but are never part of the
  data model, so they are not preserved across a read/write.

## XML profile

XML is far more expressive than data needs to be, so dataspec supports a
restricted **data-XML** profile: elements only, used purely to hold tree-shaped
data. Attributes, mixed content, namespaces, and CDATA constructs are **not**
part of the model. See [XML](xml.md) for the details and the rationale.

## Per-format pages

- **[JSON](json.md)** — the baseline; no dependencies.
- **[YAML](yaml.md)** — the JSON-compatible core of YAML.
- **[TOML](toml.md)** — native dates, no `null`, top-level object required.
- **[XML](xml.md)** — the data-XML profile, and how it maps to objects/arrays.
