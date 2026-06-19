# XML

XML can express far more than tree-shaped data — attributes, mixed text and
markup, namespaces, processing instructions. dataspec supports a deliberately
narrow **data-XML** profile: elements only, used purely to carry the same
Documents as the other formats.

Install `pip install defusedxml` so parsing is hardened against entity-expansion
and external-entity attacks. If it isn't installed, the standard library is used
as a fallback.

```python
from dataspec import read_xml, write_xml

read_xml("<r><name>Ann</name><age>30</age></r>")
# {'name': 'Ann', 'age': 30}

print(write_xml({"name": "Ann", "age": 30}, root="person"))
# <person>
#   <name>Ann</name>
#   <age>30</age>
# </person>
```

## How it maps

- An **element with child elements** is an object; each child tag is a field.
- **Repeated child tags** become an array, in document order:

  ```python
  read_xml("<r><item>1</item><item>2</item><other>x</other></r>")
  # {'item': [1, 2], 'other': 'x'}
  ```

- A **leaf element** is a scalar — its text content.
- `write_xml` wraps the document in a root element; set its name with
  `root="..."` (default `"root"`).

## What's supported

- Objects and (named) arrays nested to any depth.
- Scalars as element text.
- The `null` rule shared with TOML: a `null` field is omitted; a `null` array
  item or top-level `null` is a `WriteError` (`strict=True` also rejects omitted
  fields).

## Limitations

The profile is intentionally small. These are **not** part of the model:

| Not supported | Behaviour |
|---|---|
| Attributes (`<a x="1">`) | `ParseError` on read |
| Mixed content (text *and* elements together) | `ParseError` on read |
| Namespaces | the prefix is **stripped** (`<n:a>` reads as `a`) |
| Top-level array | `WriteError` — the root must be an object |
| Nested / bare arrays (array of arrays) | `WriteError` — a list needs a tag name |

If your XML uses attributes, transform it first (for example with XSLT) into an
attribute-free shape, then read that.

Because XML element text is **untyped**, scalar types are recovered with
best-effort guessing on read:

```python
read_xml("<r><n>30</n><ok>true</ok><s>x</s></r>")
# {'n': 30, 'ok': True, 's': 'x'}
```

This means a string that looks like a number (`"30"`) comes back as a number.
Dates come back as plain strings (they aren't guessed). When exact scalar types
matter, validate against a schema after reading, or prefer JSON/TOML.

## Round-trip behaviour

A Document made of objects, named arrays, and scalars round-trips through XML:

```python
data = {"name": "Ann", "age": 30, "tags": ["x", "y"], "addr": {"city": "HK"}}
read_xml(write_xml(data, root="rec")) == data      # True
```

The caveats above are the exceptions: numeric-looking strings are retyped as
numbers, and dates return as strings.
