"""Demo 4 — Schema version backward-compatibility checking.

Mirrors the paper's xCBL experiment: a new schema version is backward compatible
with the old one only if every old instance is still valid — i.e. the old schema
is a *subschema* of the new one.  ``subschema_sa`` pinpoints exactly where
compatibility breaks.
"""
from _bootstrap import header
from src import SchemaAutomaton, HLang, MapModel, VDom, subschema_sa


def v1() -> SchemaAutomaton:
    """v1: an Address with {street, city}; postalCode optional."""
    sa = SchemaAutomaton("addr")
    sa.add_state("addr", MapModel.of(required=["street", "city"],
                                     optional=["postalCode"]), VDom.null())
    sa.add_state("street", HLang.epsilon_lang(), VDom.strs())
    sa.add_state("city", HLang.epsilon_lang(), VDom.strs())
    sa.add_state("postalCode", HLang.epsilon_lang(), VDom.strs())
    sa.add_transition("addr", "street", "street")
    sa.add_transition("addr", "city", "city")
    sa.add_transition("addr", "postalCode", "postalCode")
    return sa


def v2_compatible() -> SchemaAutomaton:
    """v2a: adds an optional 'country' field — purely additive, compatible."""
    sa = v1()
    sa.add_state("country", HLang.epsilon_lang(), VDom.strs())
    sa.set_content("addr", MapModel.of(
        required=["street", "city"], optional=["postalCode", "country"]))
    sa.add_transition("addr", "country", "country")
    return sa


def v2_breaking() -> SchemaAutomaton:
    """v2b: makes 'postalCode' REQUIRED — breaks old instances that omit it."""
    sa = v1()
    sa.set_content("addr", MapModel.of(
        required=["street", "city", "postalCode"]))
    return sa


def main() -> None:
    header("v1  ⊆  v2 (added optional 'country')?")
    rep = subschema_sa(v1(), v2_compatible())
    print("Backward compatible:", rep.is_compatible)
    print("  → every v1 document is still valid under v2a.")

    header("v1  ⊆  v2 (made 'postalCode' required)?")
    rep = subschema_sa(v1(), v2_breaking())
    print("Backward compatible:", rep.is_compatible)
    print(rep)
    print("  → v1 documents without postalCode are rejected by v2b: NOT compatible.")


if __name__ == "__main__":
    main()
