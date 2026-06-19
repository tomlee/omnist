# FAQ

### Do `read_*` functions take a file path or a string?

A **string**. Read the file yourself and pass its text:

```python
from pathlib import Path
from dataspec import read_toml
doc = read_toml(Path("config.toml").read_text())
```

This keeps the API unambiguous and lets you read from anywhere — a file, a
request body, a database column.

### Why did converting to TOML or XML raise a `WriteError`?

Those formats can't represent everything JSON and YAML can. The usual causes:

- a `null` array item or top-level `null` (TOML/XML have no null);
- a top-level array or scalar (TOML/XML need a top-level object);
- a nested/bare array in XML (a list needs an element name).

This is the "lossless, or a clear error" guarantee at work — see
[Formats](formats/overview.md).

### What happens to `null` when I write TOML or XML?

A `null` **object field** is dropped from the output. A `null` **array item** or
a **top-level** `null` is a `WriteError`, because silently dropping it would
change the data. Pass `strict=True` to also reject dropped fields.

### Why does my numeric string come back as a number from XML?

XML element text is untyped, so dataspec guesses types on read: `"30"` becomes
`30`, `"true"` becomes `True`. A string that looks like a number will be retyped.
If exact types matter, use JSON or TOML, or validate against a schema after
reading. See [XML](formats/xml.md).

### My dates became strings after a round-trip. Is that a bug?

No. JSON and XML have no date type, so dates are written as ISO-8601 strings and
read back as strings. Schemas with `date` / `time` / `datetime` accept those
strings, so validation still works. TOML keeps dates as native values.

### How do I describe an object with arbitrary keys (a map)?

Use an index signature: `{ [string]: T }`. For example `{ [string]: integer }`
matches `{"jan": 1, "feb": 2}`. You can mix known fields with a map for the rest.
See [Maps](schema.md#maps).

### How do I allow extra/unknown fields?

End the object with `...`: `{ id: string, ... }` checks `id` and allows any other
keys. For a field whose contents you don't want to constrain at all, use `any`.

### Can a schema say "either this shape or that shape"?

Not for structures. Unions (`|`) work for scalars and enums, but there are no
structural unions. Model the variants as one open or `any`-valued object, or
validate against each candidate schema separately. See
[Limitations](schema.md#limitations).

### Is YAML support the whole language?

It's the JSON-compatible core — mappings, sequences, and standard scalars, via
the safe loader. Non-string keys and self-referential anchors are rejected on
read because they don't map to a plain Document. See [YAML](formats/yaml.md).

### Is reading XML safe against malicious input?

Install `defusedxml` (`pip install defusedxml`) and dataspec uses it
automatically, guarding against entity-expansion ("billion laughs") and
external-entity attacks. Without it, the standard library is used as a fallback.

### Which Python versions are supported?

Python **3.11 and newer** — dataspec uses the standard-library `tomllib`, which
arrived in 3.11.
