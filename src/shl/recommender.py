from typing import List, Dict, Any, Tuple
import os
import json
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from rank_bm25 import BM25Okapi
from .catalog_schema import Assessment
from .indexer import load_catalog, build_text, COLLECTION_NAME, CHROMA_DIR, MODEL_NAME


def tokenize(t: str) -> List[str]:
    return [x.lower() for x in t.split() if x.strip()]


class Recommender:
    def __init__(self):
        self.model = SentenceTransformer(MODEL_NAME)
        self.client = chromadb.PersistentClient(path=CHROMA_DIR, settings=Settings(anonymized_telemetry=False))
        self.col = self.client.get_or_create_collection(name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"})
        self.catalog = load_catalog()
        self.doc_map = {a.id: build_text(a) for a in self.catalog}
        corpus = [tokenize(self.doc_map[a.id]) for a in self.catalog]
        self.bm25 = BM25Okapi(corpus) if corpus else None
        self.id_order = [a.id for a in self.catalog]
        self.meta_map = {a.id: {"name": a.name, "url": a.url, "type": a.type} for a in self.catalog}

    def hybrid_candidates(self, query: str, n: int = 50) -> List[Tuple[str, float]]:
        if not self.catalog:
            return []
        qe = self.model.encode([query], normalize_embeddings=True, show_progress_bar=False)[0]
        res = self.col.query(query_embeddings=[qe.tolist()], n_results=min(n, 200))
        ids = res["ids"][0]
        sims = res["distances"][0]
        sem = {ids[i]: 1.0 - sims[i] for i in range(len(ids))}
        toks = tokenize(query)
        lex = {}
        if self.bm25 is not None:
            scores = self.bm25.get_scores(toks)
            lex = {self.id_order[i]: float(scores[i]) for i in range(len(self.id_order))}
            m = float(scores.max()) if hasattr(scores, "max") and scores.max() > 0 else 1.0
            for k in lex:
                lex[k] = lex[k] / m
        merged = {}
        for k in sem:
            merged[k] = 0.7 * sem[k] + 0.3 * lex.get(k, 0.0)
        for k in lex:
            if k not in merged:
                merged[k] = 0.3 * lex[k]
        items = list(merged.items())
        items.sort(key=lambda x: x[1], reverse=True)
        return items[:n]

    def balance(self, items: List[Tuple[str, float]], k: int = 10) -> List[Dict[str, Any]]:
        out = []
        k_quota = max(2, k // 2)
        p_quota = k - k_quota
        k_count = 0
        p_count = 0
        seen_names = set()
        for idv, sc in items:
            meta = self.meta_map.get(idv)
            if not meta:
                continue
            name = meta["name"]
            typ = meta.get("type", "")
            if typ == "K" and k_count >= k_quota:
                continue
            if typ == "P" and p_count >= p_quota:
                continue
            key = name.lower()
            if key in seen_names:
                continue
            seen_names.add(key)
            out.append({"name": name, "url": meta["url"], "type": typ, "score": sc})
            if typ == "K":
                k_count += 1
            elif typ == "P":
                p_count += 1
            if len(out) >= k:
                break
        i = 0
        while len(out) < k and i < len(items):
            idv, sc = items[i]
            i += 1
            meta = self.meta_map.get(idv)
            if not meta:
                continue
            name = meta["name"]
            key = name.lower()
            if key in seen_names:
                continue
            seen_names.add(key)
            out.append({"name": name, "url": meta["url"], "type": meta.get("type", ""), "score": sc})
        return out[:k]

    def recommend(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        cands = self.hybrid_candidates(query, n=max(50, k * 5))
        return self.balance(cands, k=k) if cands else []
