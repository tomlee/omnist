# API reference

Everything below is importable directly from `dataspec`:

```python
from dataspec import read_json, parse_schema, infer, WriteError   # etc.
```

## Reading and writing formats

Each `read_*` takes a **string** and returns a Document. Each `write_*` takes a
Document and returns a **string**.

| Function | Notes |
|---|---|
| `read_json(text)` | — |
| `write_json(doc, *, indent=None, sort_keys=False, strict=False, report=None)` | `indent` pretty-prints |
| `check_json(doc)` | simulate the write; return a `WriteReport`, no output |
| `read_yaml(text)` | needs `pyyaml` |
| `write_yaml(doc, *, sort_keys=False, strict=False, report=None)` | needs `pyyaml` |
| `check_yaml(doc)` | needs `pyyaml` |
| `read_toml(text)` | stdlib `tomllib` |
| `write_toml(doc, *, strict=False, report=None, null_style="omit", wrap_key="value")` | needs `tomli_w` |
| `check_toml(doc, *, null_style="omit", wrap_key="value")` | needs `tomli_w` |
| `read_xml(text)` | `defusedxml` recommended |
| `write_xml(doc, *, root="root", strict=False, report=None, null_style="omit", wrap_key="value")` | `root` names the wrapper element |
| `check_xml(doc, *, root="root", null_style="omit", wrap_key="value")` | — |

All writers are **lenient by default**: an unrepresentable value is adjusted and
recorded. `report=` collects the adjustments, `strict=True` raises a `WriteError`
(with `.report`) on any of them, and `check_*` returns the report without
writing. See [Formats](formats/overview.md) for what each can represent and the
full list of adjustment codes.

**`WriteReport`** — `.adjustments` (list of `Adjustment`), `.warnings`,
`.errors`; `bool(report)` is `True` when there are no errors.
**`Adjustment`** — a `NamedTuple(path, code, message, severity)`.

## Schemas

**`parse_schema(text) -> Schema`** — parse DSL text into a schema. Undefined
type references raise `SchemaError`. `Schema.parse(text)` is the same thing.

**`to_dsl(schema) -> str`** — serialize a schema back to DSL text. Also available
as `schema.to_dsl()`.

**`infer(samples, open_objects=False) -> Schema`** — draft a schema from example
Documents. See [Inferring schemas](infer.md).

### `Schema`

| Member | Description |
|---|---|
| `Schema(root, types=None)` | construct from a root `Type` and a dict of named types |
| `Schema.parse(text)` | classmethod; parse DSL text |
| `schema.validate(doc) -> ValidationResult` | check a document |
| `schema.accepts(doc) -> bool` | shortcut for `validate(doc).ok` |
| `schema.compatible_with(other) -> bool` | every doc this accepts, `other` accepts too |
| `schema.equivalent(other) -> bool` | both accept exactly the same docs |
| `schema.normalize() -> Schema` | merge identical named types |
| `schema.to_dsl() -> str` | serialize to DSL text |
| `schema.root`, `schema.types` | the root type and named-type dict |

### `ValidationResult`

| Member | Description |
|---|---|
| `result.ok` | `True` if valid |
| `bool(result)` | same as `.ok` |
| `result.errors` | list of `Error` |
| `str(result)` | readable multi-line summary |

### `Error`

A `NamedTuple` with `.path` (e.g. `$.items[0].id`) and `.message`. It also
unpacks as `(path, message)`.

## Schema types

For building schemas in code instead of with the text language. All are
subclasses of `Type`, and any type accepts `nullable=True`.

| Class | Constructor | Describes |
|---|---|---|
| `ScalarType` | `ScalarType(kinds, nullable=False, enum=None)` | a scalar; `kinds` is a set of kind constants |
| `ArrayType` | `ArrayType(item, min=0, max=None, nullable=False)` | an array of `item` |
| `ObjectType` | `ObjectType(fields, rest=None, nullable=False)` | an object; `fields` maps names to `Field` |
| `Field` | `Field(type, required)` | one object field |
| `AnyType` | `AnyType()` | matches anything, including null |
| `RefType` | `RefType(name, nullable=False)` | a reference to a named type |

`ObjectType.rest` controls extra keys: `None` = closed, `AnyType()` = open,
any other type = a map of that value type. `ObjectType.of(required=..., optional=...,
rest=...)` is a convenience builder.

The scalar **kind constants** are `STRING`, `INTEGER`, `NUMBER`, `BOOLEAN`,
`DATE`, `TIME`, `DATETIME`.

```python
from dataspec import Schema, ObjectType, ScalarType, Field, STRING, INTEGER

schema = Schema(ObjectType({
    "name": Field(ScalarType({STRING}), required=True),
    "age":  Field(ScalarType({INTEGER}), required=False),
}))
schema.validate({"name": "Ann"}).ok        # True
```

## Exceptions

All inherit from `DataspecError`, so you can catch everything with one `except`.

| Exception | Raised when |
|---|---|
| `DataspecError` | base class |
| `SchemaError` | a schema is invalid (bad DSL, unknown type reference) |
| `ParseError` | a document can't be read (outside a format's supported profile) |
| `WriteError` | a document can't be represented in the target format |
