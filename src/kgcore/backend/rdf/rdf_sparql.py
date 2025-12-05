from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, List, Tuple, Union

import rdflib
import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
from kgcore.backend.rdf.rdfbackend import RDFBackend

Triple = Tuple[rdflib.term.Node, rdflib.term.Node, rdflib.term.Node]


@dataclass
class SparqlAuth:
    username: str
    password: str
    auth_type: str = "digest"  # "basic" or "digest"

    def to_requests_auth(self):
        t = (self.auth_type or "").lower()
        if t == "basic":
            return HTTPBasicAuth(self.username, self.password)
        if t == "digest":
            return HTTPDigestAuth(self.username, self.password)
        raise ValueError(f"Unsupported auth_type={self.auth_type!r}. Use 'basic' or 'digest'.")


class RDFSparqlBackend(RDFBackend):
    """
    SPARQL endpoint backend (Virtuoso-friendly) using `requests`.

    Works well with endpoints like:
      - http://localhost:18890/sparql       (public SELECT)
      - http://localhost:18890/sparql-auth  (authenticated SELECT/UPDATE)

    Notes:
      - Uses application/sparql-update for updates (POST).
      - Uses GET by default for SELECT/ASK; POST also supported if you prefer.
    """

    def __init__(
        self,
        endpoint: str,
        *,
        update_endpoint: Optional[str] = None,
        auth: Optional[SparqlAuth] = None,
        default_graph: Optional[str] = None,
        timeout_s: float = 30.0,
        extra_params: Optional[dict] = None,
    ):
        self.endpoint = endpoint.rstrip("/")
        self.update_endpoint = (update_endpoint or endpoint).rstrip("/")
        self.auth = auth
        self.default_graph = default_graph
        self.timeout_s = timeout_s
        self.extra_params = extra_params or {}

        # Not used like RDFLibBackend, but keeps interface expectations sane.
        self.graph = None

    @property
    def name(self) -> str:
        return "sparql-endpoint"

    def connect(self) -> None:
        # lightweight connectivity check
        self.query_sparql("SELECT * WHERE { ?s ?p ?o } LIMIT 1")

    def close(self) -> None:
        pass

    # ---- helpers ----

    def _requests_auth(self):
        return self.auth.to_requests_auth() if self.auth else None

    def _triple_to_n3(self, t: rdflib.term.Node) -> str:
        # n3() renders proper SPARQL terms for URIRef/BNode/Literal
        return t.n3()

    def _triples_to_sparql_data(self, triples: Iterable[Triple]) -> str:
        parts = []
        for s, p, o in triples:
            parts.append(f"{self._triple_to_n3(s)} {self._triple_to_n3(p)} {self._triple_to_n3(o)} .")
        return "\n".join(parts)

    def _wrap_graph(self, data_block: str) -> str:
        if self.default_graph:
            return f"GRAPH <{self.default_graph}> {{\n{data_block}\n}}"
        return data_block

    def _http_select(self, query: str) -> dict:
        params = {"query": query, **self.extra_params}
        headers = {"Accept": "application/sparql-results+json"}
        r = requests.get(
            self.endpoint,
            params=params,
            headers=headers,
            auth=self._requests_auth(),
            timeout=self.timeout_s,
        )
        # Virtuoso often returns helpful body on 4xx/5xx:
        if r.status_code != 200:
            raise RuntimeError(f"SPARQL query failed ({r.status_code}): {r.text}")
        return r.json()

    def _http_update(self, update: str) -> None:
        headers = {"Content-Type": "application/sparql-update"}
        r = requests.post(
            self.update_endpoint,
            data=update.encode("utf-8"),
            headers=headers,
            auth=self._requests_auth(),
            timeout=self.timeout_s,
        )
        # Virtuoso may return 200 or 204 for success depending on config; accept both.
        if r.status_code not in (200, 204):
            raise RuntimeError(f"SPARQL update failed ({r.status_code}): {r.text}")

    # ---- RDFBackend interface ----

    def insert_triples(self, triples: Iterable[Triple]) -> None:
        data = self._triples_to_sparql_data(triples)
        if not data.strip():
            return
        update = f"INSERT DATA {{\n{self._wrap_graph(data)}\n}}"
        self._http_update(update)

    def delete_triples(self, triples: Iterable[Triple]) -> None:
        data = self._triples_to_sparql_data(triples)
        if not data.strip():
            return
        update = f"DELETE DATA {{\n{self._wrap_graph(data)}\n}}"
        self._http_update(update)

    def list_triples(self, s, p, o) -> List[Triple]:
        # Pure SPARQL endpoints can't stream triples like a local rdflib.Graph.
        # We emulate via SELECT.
        s_term = self._triple_to_n3(s) if s is not None else "?s"
        p_term = self._triple_to_n3(p) if p is not None else "?p"
        o_term = self._triple_to_n3(o) if o is not None else "?o"

        where = f"{s_term} {p_term} {o_term} ."
        if self.default_graph:
            where = f"GRAPH <{self.default_graph}> {{ {where} }}"

        q = f"SELECT ?s ?p ?o WHERE {{ {where} }}"

        res = self._http_select(q)
        bindings = res.get("results", {}).get("bindings", [])
        out: List[Triple] = []
        for b in bindings:
            out.append((
                rdflib.term.Node.from_n3(f"<{b['s']['value']}>") if b['s']['type'] == 'uri' else rdflib.BNode(b['s']['value']),
                rdflib.term.Node.from_n3(f"<{b['p']['value']}>") if b['p']['type'] == 'uri' else rdflib.BNode(b['p']['value']),
                self._binding_to_node(b['o']),
            ))
        return out

    def _binding_to_node(self, binding: dict) -> rdflib.term.Node:
        t = binding.get("type")
        v = binding.get("value")
        if t == "uri":
            return rdflib.URIRef(v)
        if t == "bnode":
            return rdflib.BNode(v)
        if t == "literal":
            dt = binding.get("datatype")
            lang = binding.get("xml:lang") or binding.get("lang")
            if dt:
                return rdflib.Literal(v, datatype=rdflib.URIRef(dt))
            if lang:
                return rdflib.Literal(v, lang=lang)
            return rdflib.Literal(v)
        # fallback
        return rdflib.Literal(v)

    def query_sparql(self, query: str):
        """
        Returns:
          - For SELECT/ASK: parsed JSON dict
          - For updates: executes and returns None
        """
        q0 = (query or "").lstrip().upper()
        if q0.startswith(("INSERT", "DELETE", "WITH", "LOAD", "CLEAR", "CREATE", "DROP", "MOVE", "COPY", "ADD")):
            self._http_update(query)
            return None

        # SELECT / ASK (and many endpoints return JSON only for these reliably)
        return self._http_select(query)


# from __future__ import annotations

# from typing import Iterable, Optional, List, Tuple
# import rdflib
# from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
# from kgcore.backend.rdf.rdfbackend import RDFBackend


# import urllib.request
# from urllib.request import HTTPPasswordMgrWithDefaultRealm, HTTPDigestAuthHandler


# Triple = Tuple[rdflib.term.Node, rdflib.term.Node, rdflib.term.Node]


# class RDFSparqlBackend(RDFBackend):
#     """
#     RDF backend backed by a remote SPARQL 1.1 endpoint (Virtuoso, Fuseki, etc.)
#     using SPARQLUpdateStore for both query and update.
#     """

#     def __init__(
#         self,
#         endpoint: str,
#         *,
#         auth: Optional[tuple[str, str]] = None,
#         update_endpoint: Optional[str] = None,
#         default_graph: Optional[str] = None,
#     ):
#         # Virtuoso commonly uses the same URL for query and update (/sparql or /sparql-auth).
#         self.query_endpoint = endpoint
#         self.update_endpoint = update_endpoint or endpoint
#         self.default_graph = default_graph

#         passman = HTTPPasswordMgrWithDefaultRealm()
#         passman.add_password(None, endpoint, auth[0], auth[1])
#         digest = HTTPDigestAuthHandler(passman)
#         opener = urllib.request.build_opener(digest)
#         urllib.request.install_opener(opener)


#         # SPARQLUpdateStore is a Store; we bind a Graph to it.
#         self.store = SPARQLUpdateStore(
#             query_endpoint=self.query_endpoint,
#             update_endpoint=self.update_endpoint,
#             auth=auth,  # HTTP Basic Auth (user, pass)
#         )
#         self.graph = rdflib.Graph(store=self.store, identifier=rdflib.URIRef(default_graph) if default_graph else None)

#     @property
#     def name(self) -> str:
#         return "sparql-endpoint"

#     def connect(self) -> None:
#         # nothing to open; HTTP calls happen on demand
#         pass

#     def close(self) -> None:
#         # nothing to close
#         pass

#     def get_rdflibgraph(self) -> rdflib.Graph:
#         return self.graph

#     def query_sparql(self, query: str):
#         return self.graph.query(query)

#     def insert_triples(self, triples: Iterable[Triple]) -> None:
#         # Build a SPARQL UPDATE INSERT DATA statement.
#         # Note: for large batches, chunk triples.
#         triples_n3 = "\n".join(f"{s.n3()} {p.n3()} {o.n3()} ." for s, p, o in triples)

#         if self.default_graph:
#             update = f"INSERT DATA {{ GRAPH <{self.default_graph}> {{\n{triples_n3}\n}} }}"
#         else:
#             update = f"INSERT DATA {{\n{triples_n3}\n}}"

#         self.graph.update(update)

#     def delete_triples(self, triples: Iterable[Triple]) -> None:
#         triples_n3 = "\n".join(f"{s.n3()} {p.n3()} {o.n3()} ." for s, p, o in triples)

#         if self.default_graph:
#             update = f"DELETE DATA {{ GRAPH <{self.default_graph}> {{\n{triples_n3}\n}} }}"
#         else:
#             update = f"DELETE DATA {{\n{triples_n3}\n}}"

#         self.graph.update(update)

#     def list_triples(self, s, p, o) -> List[Triple]:
#         # Your base signature says List, but rdflib returns a generator.
#         return list(self.graph.triples((s, p, o)))

# class RDFSparqlBackend_v2():
#     pass