# kgcore/ontology.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Iterable, Optional, Set, Tuple, List


IRI = str


@dataclass
class OntClass:
    """Ontology class (rdfs:Class)."""
    iri: IRI
    label: Optional[str] = None
    comment: Optional[str] = None
    parents: Set[IRI] = field(default_factory=set)  # rdfs:subClassOf
    props: Dict[str, object] = field(default_factory=dict)


@dataclass
class Predicate:
    """Ontology property (rdf:Property / rdf:type-specific)."""
    iri: IRI
    label: Optional[str] = None
    comment: Optional[str] = None
    domain: Set[IRI] = field(default_factory=set)  # rdfs:domain (0..n)
    range: Set[IRI] = field(default_factory=set)   # rdfs:range (0..n)
    props: Dict[str, object] = field(default_factory=dict)


class Ontology:
    """
    Minimal ontology API:
    - add/get classes and predicates
    - labels, comments, props
    - subClassOf edges
    - domain/range on predicates
    - subclass checks and ancestry
    - triple validation (subject type, predicate, object type)
    """

    def __init__(self) -> None:
        self._classes: Dict[IRI, OntClass] = {}
        self._preds: Dict[IRI, Predicate] = {}

    # ---------- Class API ----------

    def add_class(
        self,
        iri: IRI,
        *,
        label: Optional[str] = None,
        comment: Optional[str] = None,
        parents: Optional[Iterable[IRI]] = None,
        props: Optional[Dict[str, object]] = None,
    ) -> OntClass:
        """Create or update a class."""
        cls = self._classes.get(iri, OntClass(iri=iri))
        if label is not None:
            cls.label = label
        if comment is not None:
            cls.comment = comment
        if parents:
            cls.parents.update(parents)
            for p in parents:
                self._ensure_class(p)
        if props:
            cls.props.update(props)
        self._classes[iri] = cls
        return cls

    def get_class(self, iri: IRI) -> Optional[OntClass]:
        return self._classes.get(iri)

    def set_subclass(self, child: IRI, parent: IRI) -> None:
        self._ensure_class(child).parents.add(parent)
        self._ensure_class(parent)

    def set_class_label(self, iri: IRI, label: str) -> None:
        self._ensure_class(iri).label = label

    def ancestors(self, iri: IRI) -> Set[IRI]:
        """All transitive superclasses (excluding the class itself)."""
        seen: Set[IRI] = set()
        stack: List[IRI] = list(self._ensure_class(iri).parents)
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            stack.extend(self._ensure_class(cur).parents)
        return seen

    def is_subclass_of(self, child: IRI, parent: IRI) -> bool:
        if child == parent:
            return True
        return parent in self.ancestors(child)

    # ---------- Predicate API ----------

    def add_predicate(
        self,
        iri: IRI,
        *,
        label: Optional[str] = None,
        comment: Optional[str] = None,
        domain: Optional[Iterable[IRI]] = None,
        range: Optional[Iterable[IRI]] = None,
        props: Optional[Dict[str, object]] = None,
    ) -> Predicate:
        """Create or update a predicate (property)."""
        pred = self._preds.get(iri, Predicate(iri=iri))
        if label is not None:
            pred.label = label
        if comment is not None:
            pred.comment = comment
        if domain:
            pred.domain.update(domain)
            for d in domain:
                self._ensure_class(d)
        if range:
            pred.range.update(range)
            for r in range:
                self._ensure_class(r)
        if props:
            pred.props.update(props)
        self._preds[iri] = pred
        return pred

    def get_predicate(self, iri: IRI) -> Optional[Predicate]:
        return self._preds.get(iri)

    def set_domain(self, pred: IRI, domain: Iterable[IRI]) -> None:
        p = self._ensure_pred(pred)
        p.domain = set(domain)
        for d in p.domain:
            self._ensure_class(d)

    def set_range(self, pred: IRI, rng: Iterable[IRI]) -> None:
        p = self._ensure_pred(pred)
        p.range = set(rng)
        for r in p.range:
            self._ensure_class(r)

    def set_predicate_label(self, iri: IRI, label: str) -> None:
        self._ensure_pred(iri).label = label

    # ---------- Validation ----------

    def validate_triple(
        self,
        subject_type: IRI,
        predicate: IRI,
        object_type: IRI,
    ) -> Tuple[bool, str]:
        """
        Validate (subject_type, predicate, object_type) against domain/range.
        - Accepts subclasses (subject/object may be subclass of declared domain/range).
        - Empty domain/range means 'unspecified' -> treated as valid.
        Returns (ok, reason).
        """
        p = self._preds.get(predicate)
        if p is None:
            return False, f"Unknown predicate: {predicate}"

        # Domain
        if p.domain:
            if not any(self.is_subclass_of(subject_type, d) for d in p.domain):
                return (
                    False,
                    f"Domain violation: {subject_type} !⊑ any({sorted(p.domain)})",
                )

        # Range
        if p.range:
            if not any(self.is_subclass_of(object_type, r) for r in p.range):
                return (
                    False,
                    f"Range violation: {object_type} !⊑ any({sorted(p.range)})",
                )

        return True, "ok"

    # ---------- Utilities ----------

    def _ensure_class(self, iri: IRI) -> OntClass:
        if iri not in self._classes:
            self._classes[iri] = OntClass(iri=iri)
        return self._classes[iri]

    def _ensure_pred(self, iri: IRI) -> Predicate:
        if iri not in self._preds:
            self._preds[iri] = Predicate(iri=iri)
        return self._preds[iri]

    def labels(self, iri: IRI) -> Optional[str]:
        """Get best label for class/predicate."""
        obj = self._classes.get(iri) or self._preds.get(iri)
        return obj.label if obj else None

    # ---------- Export (stubs you can extend) ----------

    def to_tbox(self) -> Dict[str, object]:
        """
        Export a tiny TBox-like dict. Intended for testing, not wire format.
        """
        return {
            "classes": [
                {
                    "iri": c.iri,
                    "label": c.label,
                    "comment": c.comment,
                    "parents": sorted(c.parents),
                    "props": dict(c.props),
                }
                for c in self._classes.values()
            ],
            "predicates": [
                {
                    "iri": p.iri,
                    "label": p.label,
                    "comment": p.comment,
                    "domain": sorted(p.domain),
                    "range": sorted(p.range),
                    "props": dict(p.props),
                }
                for p in self._preds.values()
            ],
        }
