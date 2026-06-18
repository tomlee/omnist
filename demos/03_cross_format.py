"""Demo 3 — One canonical schema across JSON, YAML and TOML.

Because every format collapses to the same canonical Data Tree, a schema
inferred from JSON validates equivalent YAML and TOML documents directly — no
per-format schema language required.
"""
from _bootstrap import header
from src import (
    tree_from_json, tree_from_yaml, tree_from_toml, tree_from_python,
    infer_schema,
)

JSON_SAMPLES = [
    '{"service": "api", "port": 8080, "tags": ["web"], "tls": {"enabled": true}}',
    '{"service": "db",  "port": 5432, "tags": ["store", "sql"], "tls": {"enabled": false}}',
]

YAML_DOC = """
service: cache
port: 6379
tags:
  - kv
  - memory
tls:
  enabled: true
"""

TOML_DOC = """
service = "queue"
port = 5672
tags = ["amqp"]

[tls]
enabled = false
"""


def _try(label, fn):
    try:
        return fn()
    except ImportError as exc:
        print(f"  ({label} skipped: {exc})")
        return None


def main() -> None:
    header("Infer schema from JSON, validate YAML & TOML")
    schema = infer_schema([tree_from_json(s) for s in JSON_SAMPLES])
    print(f"Inferred schema: {len(schema.states)} states (from JSON only).")

    yaml_tree = _try("YAML", lambda: tree_from_yaml(YAML_DOC))
    if yaml_tree is not None:
        print("YAML document valid against JSON-inferred schema:",
              schema.validate(yaml_tree).ok)

    toml_tree = _try("TOML", lambda: tree_from_toml(TOML_DOC))
    if toml_tree is not None:
        print("TOML document valid against JSON-inferred schema:",
              schema.validate(toml_tree).ok)

    header("A format-correct but schema-invalid document is still caught")
    bad = tree_from_python({"service": "x", "port": "not-an-int",
                            "tags": ["y"], "tls": {"enabled": True}})
    res = schema.validate(bad)
    print(res)


if __name__ == "__main__":
    main()
