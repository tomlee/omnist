"""Demo 1 — The CIKM 2010 paper's XML examples.

Builds Schema Automata SA1, SA2 (its minimal form) and SA3 (a Quote-only
subschema) by hand, then demonstrates the four schema computations:
minimization, equivalence, subschema testing, and subschema extraction.
"""
from _bootstrap import header
from src import (
    DataTree, SchemaAutomaton, HLang, VDom,
    minimize_sa, equivalent_sa, subschema_sa, extract_subschema,
)


def quote_doc() -> DataTree:
    dt = DataTree("n0", "")
    for nid in ("n1", "n2", "n3"):
        dt.add_node(nid, "")
    dt.add_node("n4", "hPhone"); dt.add_node("n5", "499.9")
    dt.add_node("n6", "iMat");   dt.add_node("n7", "999.9")
    dt.add_edge("n0", "n1", "Quote")
    dt.add_edge("n1", "n2", "Line"); dt.add_edge("n1", "n3", "Line")
    dt.add_edge("n2", "n4", "Desc"); dt.add_edge("n2", "n5", "Price")
    dt.add_edge("n3", "n6", "Desc"); dt.add_edge("n3", "n7", "Price")
    return dt


def order_doc() -> DataTree:
    dt = DataTree("n0", "")
    for nid in ("n1", "n2", "n3"):
        dt.add_node(nid, "")
    dt.add_node("n4", "2"); dt.add_node("n5", "hPhone"); dt.add_node("n6", "499.9")
    dt.add_edge("n0", "n1", "Order")
    dt.add_edge("n1", "n2", "Line")
    dt.add_edge("n2", "n3", "Product"); dt.add_edge("n2", "n4", "Qty")
    dt.add_edge("n3", "n5", "Desc"); dt.add_edge("n3", "n6", "Price")
    return dt


def sa1() -> SchemaAutomaton:
    """Models XSD 1 — every complex type is anonymous (no reuse): 9 states."""
    null = VDom.null()
    sa = SchemaAutomaton("q0")
    sa.add_state("q0", HLang.parse("Quote|Order"), null)
    sa.add_state("q1", HLang.parse("Line+"), null)
    sa.add_state("q2", HLang.parse("Line+"), null)
    sa.add_state("q3", HLang.parse("Desc Price"), null)
    sa.add_state("q4", HLang.parse("Product Qty"), null)
    sa.add_state("q5", HLang.epsilon_lang(), VDom.strs())
    sa.add_state("q6", HLang.epsilon_lang(), VDom.decs())
    sa.add_state("q7", HLang.parse("Desc Price"), null)
    sa.add_state("q8", HLang.epsilon_lang(), VDom.ints())
    sa.add_transition("q0", "Quote", "q1"); sa.add_transition("q0", "Order", "q2")
    sa.add_transition("q1", "Line", "q3"); sa.add_transition("q2", "Line", "q4")
    sa.add_transition("q3", "Desc", "q5"); sa.add_transition("q3", "Price", "q6")
    sa.add_transition("q4", "Product", "q7"); sa.add_transition("q4", "Qty", "q8")
    sa.add_transition("q7", "Desc", "q5"); sa.add_transition("q7", "Price", "q6")
    return sa


def sa3() -> SchemaAutomaton:
    """Models XSD 3 — a Quote-only subschema."""
    null = VDom.null()
    sa = SchemaAutomaton("q0")
    sa.add_state("q0", HLang.parse("Quote"), null)
    sa.add_state("q1", HLang.parse("Line+"), null)
    sa.add_state("q9", HLang.parse("Desc Price"), null)
    sa.add_state("q5", HLang.epsilon_lang(), VDom.strs())
    sa.add_state("q6", HLang.epsilon_lang(), VDom.decs())
    sa.add_transition("q0", "Quote", "q1")
    sa.add_transition("q1", "Line", "q9")
    sa.add_transition("q9", "Desc", "q5"); sa.add_transition("q9", "Price", "q6")
    return sa


def main() -> None:
    A1, A3 = sa1(), sa3()

    header("Validation (Definition 3)")
    print("SA1 accepts Quote doc:", A1.accepts(quote_doc()))
    print("SA1 accepts Order doc:", A1.accepts(order_doc()))
    print("SA3 accepts Quote doc:", A3.accepts(quote_doc()), "(Quote-only)")
    print("SA3 accepts Order doc:", A3.accepts(order_doc()), "(rejected)")

    header("Minimization (Algorithm 2)")
    A2 = minimize_sa(A1)
    print(f"SA1 has {len(A1.states)} states; minimized to {len(A2.states)} "
          f"(equivalent states q3 & q7 merge).")

    header("Equivalence (Algorithm 3)")
    print("minimized(SA1) ≡ SA1 :", equivalent_sa(A2, A1))
    print("SA3 ≡ SA1            :", equivalent_sa(A3, A1), "(different languages)")

    header("Subschema testing (Algorithm 4)")
    print("SA3 ⊆ SA1 :", subschema_sa(A3, A1).is_compatible)
    rep = subschema_sa(A1, A3)
    print("SA1 ⊆ SA3 :", rep.is_compatible)
    print(rep)

    header("Subschema extraction (Algorithm 5)")
    permitted = {"Quote", "Order", "Line", "Qty", "Desc", "Price"}  # drop 'Product'
    extracted = extract_subschema(A1, permitted)
    print("Permitted symbols:", sorted(permitted))
    print("Dropping mandatory 'Product' collapses the Order branch.")
    print("extracted ≡ SA3 :", equivalent_sa(extracted, A3))


if __name__ == "__main__":
    main()
