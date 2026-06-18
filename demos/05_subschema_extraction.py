"""Demo 5 — Trimming a large schema to the part an application needs.

The paper extracts small subschemas from huge xCBL XSDs so an application that
handles only a few document types loads a fraction of the schema.  Here we infer
a schema for a broad config document, then extract a subschema that recognises
only the keys a lightweight client actually reads.
"""
import json

from _bootstrap import header
from src import (
    tree_from_python, infer_schema, extract_subschema, to_json_schema,
    subschema_sa,
)


# Two samples: the optional sections (database/cache/logging) are absent from
# the second, so inference marks them OPTIONAL — which lets us drop them during
# extraction.  service/port/features appear in both, so they stay REQUIRED.
FULL_CONFIG = {
    "service": "billing",
    "port": 8080,
    "database": {"host": "db", "port": 5432, "pool": 10},
    "cache": {"host": "redis", "ttl": 60},
    "logging": {"level": "info", "sinks": ["stdout", "file"]},
    "features": ["invoices", "refunds", "reports"],
}
MINIMAL_CONFIG = {
    "service": "billing",
    "port": 8080,
    "features": ["invoices"],
}


def main() -> None:
    header("Full inferred config schema")
    full = infer_schema([tree_from_python(FULL_CONFIG),
                         tree_from_python(MINIMAL_CONFIG)])
    content = full.get_content(full.initial)
    print(f"{len(full.states)} states. Top-level keys: "
          f"{sorted(content.symbols())}")
    print(f"Required: {sorted(content.mandatory_symbols())}")

    header("Extract a subschema for a client that reads only service/port/features")
    # NB: extraction works on the symbol alphabet; we keep the top-level keys we
    # want plus the array item marker so 'features' entries survive.
    from src import ITEM
    keep = {"service", "port", "features", ITEM}
    trimmed = extract_subschema(full, keep)
    print(f"Trimmed schema: {len(trimmed.states)} states.")
    print(json.dumps(to_json_schema(trimmed), indent=2))

    header("The trimmed schema is a genuine subschema of the full one")
    print("trimmed ⊆ full :", subschema_sa(trimmed, full).is_compatible)

    header("Validating against the trimmed schema")
    client_view = tree_from_python({"service": "billing", "port": 8080,
                                    "features": ["invoices"]})
    print("client document valid:", trimmed.validate(client_view).ok)


if __name__ == "__main__":
    main()
