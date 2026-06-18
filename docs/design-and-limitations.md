# Design & Limitations

## Why a Content Model abstraction?

The paper models the permissible children of a node with a *horizontal language*
(HLang) — a regular language over the **ordered** sequence of child-edge
symbols. That is exactly right for XML, where element order is significant. But
the other popular data formats are not all ordered:

| Format construct | Order significant? | Unique labels? |
|------------------|--------------------|----------------|
| XML element sequence | yes | no |
| JSON array / YAML sequence | yes | n/a (positional) |
| JSON object / TOML table / YAML map | **no** | **yes (keys)** |

Forcing object validation through an ordered regular language would be both
awkward (which key order do you encode?) and wrong (it would reject valid
re-orderings). So the per-state child constraint is abstracted into a
`ContentModel` interface with three implementations — ordered `HLang`, unordered
`MapModel`, leaf `ScalarModel` — sharing one interface
(`accepts`, `is_subset_of`, `canonical_key`, `mandatory_symbols`,
`remove_symbol`, `is_empty`). The five schema algorithms are written purely
against that interface, so they work identically for XML and JSON/TOML/YAML.

This is the key extension over the paper, which only addresses XML/XSD.

## Two "fits" relations, on purpose

* `VDom.is_subset_of` follows XSD/string semantics (`INTS ⊆ STRS`) and is used
  for **schema-vs-schema** subschema testing, as in the paper.
* `VDom.admits` follows data-format semantics (`1 ≠ "1"`) and is used for
  **validating a typed value**.

Keeping them separate lets the library stay faithful to the paper's XML
computations while validating typed JSON/TOML/YAML correctly.

---

## Known limitations

These are honest boundaries of the current model, each chosen to fail loudly
rather than silently produce a wrong schema.

### 1. No union / nullable-complex types

A single SA state carries **one** content model and **one** value domain, so it
cannot express `object | string`, `array | object`, or `object | null`. Schema
**inference raises `ValueError`** when a position is structurally inconsistent
across samples (including a scalar `null` co-occurring with an object/array),
rather than guessing. Scalar nullability (`string | null`) *is* supported via
nullable value domains, because that stays within a single scalar state.

*Possible extension:* introduce explicit union states (a state that delegates to
several alternative content models / domains).

### 2. Arrays observed only empty

If every sample array at a position is empty, no element type can be inferred, so
the position infers to **empty-sequence-only** and a later non-empty array is
rejected. This keeps the automaton consistent (Definition 2) and predictable; it
is conservative by design.

### 3. Inference produces closed objects

Inferred `MapModel`s are **closed** (`additionalProperties: false`). The model
fully supports open maps — `MapModel(fields, open=True)` — but inference never
emits them, because "allow arbitrary extra keys" cannot be concluded from a
finite sample. Build open maps by hand when you want them.

### 4. XSD feature coverage

Following the paper, the Schema Automaton models the commonly-used core of XSD
(complex/simple types, element sequences, occurrence constraints, built-in
scalar types). It does **not** model open-content wildcards such as `xs:any`,
attribute-vs-element distinctions, namespaces, or identity constraints
(key/keyref). These are noted as extensions in §8 of the paper.

### 5. Performance of regular-expression tests

Equivalence and inclusion of ordered content languages are decided **exactly**
via DFA operations, which are PSPACE-complete in the worst case. For very large
ordered schemas, the paper's filtering heuristics (literal-equality short-circuit
and a PTIME weak test for simple expressions, §6) would be a worthwhile addition;
they are not yet implemented here. Unordered `MapModel` comparisons are linear.

---

## Project layout

```
src/
  nfa.py              NFA/DFA engine (Thompson, subset construction, Hopcroft)
  content_model.py    ContentModel ABC + MapModel + ScalarModel
  hlang.py            HLang — the ordered (sequence) content model
  vdom.py             value domains (STRS/INTS/DECS/BOOL/NULL/enum/nullable)
  data_tree.py        Data Tree (Definition 1)
  schema_automaton.py Schema Automaton (Definition 2) + validation (Definition 3)
  algorithms.py       Algorithms 1–5
  formats.py          JSON/YAML/TOML loaders + schema inference
  export.py           Schema Automaton → JSON-Schema-like dict
tests/
  test_paper.py       reproduces the CIKM 2010 examples
  test_formats.py     map model, loaders, inference, validation, export
demos/                five runnable, self-contained demos
docs/                 this documentation + the source paper (docs/paper/)
main.py               quick combined tour
```

## Relationship to the paper

This implementation reproduces the paper's worked examples (SA1/SA2/SA3
equivalence, subschema testing, and subschema extraction) in
`tests/test_paper.py` and `demos/01_xml_paper_examples.py`, and extends the
models with the format-agnostic Content Model, typed value domains, schema
inference, path-aware validation, and JSON-Schema export. The source paper is
included at
[`paper/Lee-Cheung-2010-XML-Schema-Computations-CIKM.pdf`](paper/Lee-Cheung-2010-XML-Schema-Computations-CIKM.pdf).
