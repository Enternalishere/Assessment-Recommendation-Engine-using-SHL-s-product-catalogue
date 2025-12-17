import os
import json
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from .catalog_schema import Assessment


CATALOG_PATH = "data/catalog.jsonl"
CHROMA_DIR = "data/chroma"
COLLECTION_NAME = "shl_assessments"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def load_catalog() -> List[Assessment]:
    items = []
    if not os.path.exists(CATALOG_PATH):
        return items
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            items.append(Assessment.from_dict(d))
    return items


def build_text(a: Assessment) -> str:
    parts = [
        a.name,
        a.description,
        "skills: " + ", ".join(a.skills),
        "tags: " + ", ".join(a.tags),
        "type: " + a.type,
    ]
    return " | ".join([p for p in parts if p])


def get_client():
    os.makedirs(CHROMA_DIR, exist_ok=True)
    client = chromadb.PersistentClient(path=CHROMA_DIR, settings=Settings(anonymized_telemetry=False))
    return client


def get_collection(client):
    col = client.get_or_create_collection(name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"})
    return col


def index() -> Dict[str, Any]:
    items = load_catalog()
    if not items:
        return {"indexed": 0}
    model = SentenceTransformer(MODEL_NAME)
    client = get_client()
    col = get_collection(client)
    ids = []
    docs = []
    metas = []
    for a in items:
        ids.append(a.id)
        docs.append(build_text(a))
        metas.append({"name": a.name, "url": a.url, "type": a.type})
    embs = model.encode(docs, normalize_embeddings=True, batch_size=64, show_progress_bar=False)
    col.delete(ids=ids)
    col.add(ids=ids, embeddings=embs.tolist(), documents=docs, metadatas=metas)
    return {"indexed": len(ids), "collection": COLLECTION_NAME}

