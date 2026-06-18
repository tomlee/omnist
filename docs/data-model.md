# Data Model Specification

This document specifies the data structures the library is built on. Two are the
formal models from the paper — the **Data Tree** and the **Schema Automaton** —
and two are the abstractions that generalise the schema model across data
formats — the **Content Model** and the **Value Domain**.

```
            data instance                         schema
        ┌───────────────────┐            ┌──────────────────────────┐
        │     Data Tree     │  ◄── validated by ──  Schema Automaton │
        │  (N,E,Y,n0,…)     │            │   (Q,X,q0,δ,Content,VDom) │
        └───────────────────┘            └──────────────────────────┘
                  ▲                                  │  per state
   JSON/YAML/TOML/XML loaders               ┌────────┴─────────┐
                                            ContentModel      VDom
                                       (children constraint) (value constraint)
```

---

## 1. Data Tree (DT)

A **Data Tree** is the canonical, format-neutral representation of one data
instance. It is the paper's Definition 1.

> A Data Tree is a 7-tuple `(N, E, Y, n0, CEdges, Val, Sym)`:
> * `N` — finite set of **data nodes** (d-nodes)
> * `E` — finite set of **data edges** (d-edges); each is an ordered pair
>   `(n_parent, n_child)`
> * `Y` — set of edge **symbols**
> * `n0 ∈ N` — the unique **root** d-node
> * `CEdges : N → E*` — the **ordered** sequence of child edges of each d-node
> * `Val : N → V` — the **value** stored at each d-node (the empty string `""`
>   denotes the null value `ε`)
> * `Sym : E → Y` — the **symbol** labelling each d-edge

Every non-root node has exactly one parent and is reachable from the root by a
unique path of edges.

### Implementation — `src/data_tree.py`

| Concept | API |
|---------|-----|
| d-node | `DNode(node_id, value, kind=None, vdom=None)` |
| d-edge | `DEdge(edge_id, parent_id, child_id, symbol)` |
| the tree | `DataTree(root_id, root_value, root_kind, root_vdom)` |
| `CEdges(n)` | `tree.child_edges(node_id)` |
| `CSeq(n)` | `tree.child_symbol_sequence(node_id)` → the ordered symbol list |
| `Val(n)` | `tree.val(node_id)` |
| `Sym(e)` | `tree.sym(edge_id)` |

Two **optional** annotations extend the paper's model to make typed, multi-format
data faithful; they are `None` for pure paper/XML usage and never required for
the core algorithms:

* `DNode.kind` — the structural role, one of `KIND_MAP`, `KIND_SEQUENCE`,
  `KIND_SCALAR`. Lets a loader distinguish an empty object from an empty array.
* `DNode.vdom` — a value-domain *hint* describing the node's own scalar type
  (e.g. the JSON value `1` carries `VDom(INTS)`), consumed by inference and by
  type-aware validation.

### How each format maps onto a Data Tree

| Format construct | Data Tree |
|------------------|-----------|
| XML element `<a>…</a>` | a d-edge with `Sym = "a"` + its child d-node |
| object / map / table | d-node of kind `MAP`; one child d-edge per key (`Sym = key`) |
| array / sequence | d-node of kind `SEQUENCE`; every child d-edge labelled with the item marker `ITEM` (`"[]"`) |
| scalar (string/number/bool/null) | leaf d-node of kind `SCALAR`, `Val` = the string form, `vdom` = the inferred type |

Example — the JSON `{"tags": ["x", "y"]}`:

```
n0 (MAP, ε)
└──tags──► n1 (SEQUENCE, ε)
            ├──[]──► n2 (SCALAR, "x")
            └──[]──► n3 (SCALAR, "y")
```

---

## 2. Schema Automaton (SA)

A **Schema Automaton** is a deterministic automaton over Data Trees — the
paper's Definition 2, generalised so a single SA can describe ordered (XML,
arrays) and unordered (objects/maps) content.

> A Schema Automaton is a 6-tuple `(Q, X, q0, δ, Content, VDom)`:
> * `Q` — finite set of **states**, each modelling a data *type*
> * `X` — finite set of **symbols** (element names / object keys / `ITEM`)
> * `q0 ∈ Q` — the **initial** state
> * `δ : Q × X → Q ∪ {⊥}` — the **transition function** (`⊥` = the implicit
>   dead state; a missing entry means `⊥`)
> * `Content : Q → ContentModel` — permissible **children** of a node in this
>   state (the paper's per-state *horizontal language*, here generalised)
> * `VDom : Q → ValueDomain` — permissible scalar **value** of a node in this
>   state

There is no explicit set of final states: a state is *accepting of a leaf* when
its content model accepts the empty sequence.

### Validation — when does an SA accept a Data Tree? (Definition 3)

An SA `A` accepts a Data Tree `T` iff there is a unique binding `Bind : N → Q`
of every node to a state such that, recursively from the root (`Bind(n0)=q0`):

1. **Structure** — `CSeq(n) ∈ Content(Bind(n))` (the child symbol sequence is
   permitted), and (optionally) the node's `kind` matches the content model's
   kind;
2. **Value** — `Val(n)` is admissible in `VDom(Bind(n))`;
3. **Transitions** — for each child edge `(n, n_i)` with symbol `a`,
   `Bind(n_i) = δ(Bind(n), a)` (and that transition is not `⊥`).

### Implementation — `src/schema_automaton.py`

```python
sa = SchemaAutomaton("q0")
sa.add_state("q0", content=MapModel.of(required=["host"]), vdom=VDom.null())
sa.add_state("host", content=ScalarModel(), vdom=VDom.strs())   # scalar leaf
sa.add_transition("q0", "host", "host")

sa.accepts(tree)             # -> bool          (Definition 3)
sa.validate(tree)            # -> ValidationResult with path-aware errors
```

> **Leaf content models.** For scalar leaves of data loaded via `tree_from_*`
> (whose nodes carry `kind=SCALAR`), use `ScalarModel()`. The XML idiom
> `HLang.epsilon_lang()` is an *empty element* (kind `SEQUENCE`) and is meant for
> hand-built XML trees whose nodes have no `kind`. The optional structural-kind
> check rejects a `SEQUENCE` content model against a `SCALAR` node.

The **consistency invariant** (Definition 2) is maintained by all algorithms and
the inferencer: if a symbol `a` occurs in some string of `Content(q)`, then
`δ(q, a)` must be a real state (not `⊥`); conversely symbols never occurring in
the content language have no transition.

---

## 3. Content Model

The **Content Model** is the abstraction that makes the schema format-agnostic.
In the paper, a state's children are described by a *horizontal language* — a
regular language over the **ordered** child-symbol sequence. That is correct for
XML, but JSON/TOML/YAML objects are **unordered** with **unique keys**.

`ContentModel` (`src/content_model.py`) is the common interface; three
implementations cover the data formats:

| Model | Order | Models | Key idea |
|-------|-------|--------|----------|
| `HLang` (a *SequenceModel*) | ordered | XML element sequences, arrays | regular language over symbols, via an NFA/DFA |
| `MapModel` | unordered, unique keys | JSON objects, TOML tables, YAML maps | a record of fields, each *required* or *optional*; optionally *open* to extra keys |
| `ScalarModel` | leaf | scalar values | accepts only the empty sequence; the constraint lives in the `VDom` |

Every content model exposes exactly what the algorithms need, so the algorithms
never branch on data format:

```
accepts(sequence)        membership: is this child-symbol sequence permitted?
symbols()                all symbols that may appear
mandatory_symbols()      symbols present in every accepted (non-empty) sequence
remove_symbol(a)         the language minus all sequences containing a
is_empty()               does it accept nothing at all?
is_subset_of(other)      language inclusion
canonical_key()          hashable; equal keys ⇔ equal languages
language_equals(other)   language equality
```

### `HLang` regular-expression syntax

`HLang.parse(pattern)` accepts:

| Syntax | Meaning |
|--------|---------|
| `A`, `<A>` | a single symbol named `A` |
| `A B` | concatenation (ordered) |
| `A|B` | alternation |
| `A*` `A+` `A?` | Kleene star / plus / optional |
| `A{2,5}` | bounded repetition (`{2,*}` = 2-or-more) |
| `(…)` | grouping |
| `epsilon` | the empty sequence |

Example: `HLang.parse("Desc Price")`, `HLang.parse("Line+")`,
`HLang.parse("Quote|Order")`.

### `MapModel`

```python
MapModel.of(required=["host", "port"], optional=["tls"], open=False)
```

* accepts any *unordered, duplicate-free* set of keys that includes all
  `required` keys and no key outside `required ∪ optional` (unless `open`);
* `mandatory_symbols()` = the required keys;
* `remove_symbol(k)` drops an optional key, or — if `k` was required — yields the
  **empty** map (no document can satisfy it), which is how extraction detects
  that a key cannot be removed.

---

## 4. Value Domain (VDom)

A **Value Domain** constrains the scalar value of a d-node. Named domains mirror
the scalar types common to XML simple types and JSON/TOML/YAML scalars:

| Domain | Admits | Maps to |
|--------|--------|---------|
| `STRS` | any string | `xs:string`, JSON string |
| `INTS` | integer values | `xs:int`, JSON/TOML integer |
| `DECS` | decimal / float values | `xs:decimal`, JSON/TOML float |
| `BOOL` | `true` / `false` | `xs:boolean`, JSON/TOML bool |
| `NULL` | only the null value `ε` | complex/map/sequence nodes |
| finite enum | a fixed set of strings | enumerations |

A domain may also be **nullable** (admits the null value in addition to its base
type) — needed for *"string or null"* style fields.

### Two notions of "fits", deliberately kept separate

* **`is_subset_of` (XSD/string semantics)** — used for *schema-vs-schema*
  subschema testing per the paper. Here every integer string is also a string,
  so `INTS ⊆ STRS`.
* **`admits` (data-format semantics)** — used for *validating a typed value*. In
  JSON, `1` and `"1"` are different types, so a number is **not** admitted where
  a string is expected. Validation uses `admits` when a node carries a type hint
  (`node.vdom`) and falls back to string-based `contains` otherwise (the paper's
  untyped XML model).

`VDom.union(a, b)` computes the least domain covering both (used by inference):
numeric widening `INTS ∪ DECS = DECS`, nullability `X ∪ NULL = X?`, and a fall
back to `STRS` for unrelated kinds.

---

## 5. Summary of correspondences

| Paper concept | This library |
|---------------|--------------|
| Data Tree (Def. 1) | `DataTree`, `DNode`, `DEdge` |
| Schema Automaton (Def. 2) | `SchemaAutomaton` |
| Acceptance (Def. 3) | `SchemaAutomaton.accepts` / `.validate` |
| Horizontal language (HLang) | `HLang` (a `ContentModel`) |
| Value domain (VDom) | `VDom` |
| *(new)* unordered content | `MapModel` |
| *(new)* typed value checking | `VDom.admits`, `DNode.vdom` |
