"""Demo 2 — Infer a schema from JSON samples, then validate documents.

Shows:
  * inferring a canonical schema from example data,
  * exporting it as a readable JSON-Schema-like dict,
  * validating good and bad documents with path-aware error messages.
"""
import json

from _bootstrap import header
from src import tree_from_json, tree_from_python, infer_schema, to_json_schema


SAMPLES = [
    '{"id": 1, "name": "Ann",  "email": "ann@x.io", "roles": ["admin", "user"]}',
    '{"id": 2, "name": "Bob",  "roles": ["user"]}',
    '{"id": 3, "name": "Cara", "email": "cara@x.io", "roles": []}',
]


def main() -> None:
    header("Inferring a schema from 3 JSON user records")
    trees = [tree_from_json(s) for s in SAMPLES]
    schema = infer_schema(trees)
    print(f"Schema has {len(schema.states)} states.")
    print("\nInferred JSON-Schema view:")
    print(json.dumps(to_json_schema(schema), indent=2))
    # Note: 'email' appears in only 2/3 samples -> optional;
    #       'roles' is an array of strings, allowed empty (item*) because one
    #       sample had [].

    header("Validating documents")
    good = tree_from_python({"id": 9, "name": "Dee", "roles": ["user"]})
    print("• valid doc (no optional email):")
    print("   ", schema.validate(good))

    print("\n• missing required 'name':")
    bad1 = tree_from_python({"id": 9, "roles": ["user"]})
    print("   ", str(schema.validate(bad1)).replace("\n", "\n    "))

    print("\n• wrong types + unexpected key:")
    bad2 = tree_from_python({"id": "nine", "name": "Dee", "roles": [1, 2], "x": True})
    print("   ", str(schema.validate(bad2)).replace("\n", "\n    "))


if __name__ == "__main__":
    main()
