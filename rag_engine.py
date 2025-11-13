import os
import json
import numpy as np
import faiss
from tqdm import tqdm
from sentence_transformers import SentenceTransformer

from config import DOCS_DIR, INDEX_PATH, CHUNKS_PATH, EMBED_MODEL_NAME


def read_text(path):
    try:
        return open(path, "r", encoding="utf-8").read()
    except:
        return open(path, "r", encoding="latin-1").read()


def iter_text_files(root):
    for r, _, fs in os.walk(root):
        for f in fs:
            if any(f.endswith(ext) for ext in (".md", ".txt", ".rst", ".py")):
                yield os.path.join(r, f)


def chunk_text(text, size=600, overlap=120):
    tokens = text.split()
    chunks = []
    i = 0
    while i < len(tokens):
        chunks.append(" ".join(tokens[i:i + size]))
        i += (size - overlap)
    return chunks


class RAGEngine:
    def __init__(self,
                 index_path=INDEX_PATH,
                 chunks_path=CHUNKS_PATH,
                 model_name=EMBED_MODEL_NAME):
        if not os.path.exists(index_path):
            raise FileNotFoundError(index_path)
        if not os.path.exists(chunks_path):
            raise FileNotFoundError(chunks_path)

        self.index = faiss.read_index(index_path)
        self.chunks = json.load(open(chunks_path))
        self.model = SentenceTransformer(model_name, cache_folder="./.cache")

    @classmethod
    def build_from_corpus(cls):
        os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)

        texts, meta = [], []

        print(f"[KB] scanning docs from {DOCS_DIR}")
        for p in iter_text_files(DOCS_DIR):
            txt = read_text(p)
            for c in chunk_text(txt):
                texts.append(c)
                meta.append({"text": c, "source": p})

        print(f"[KB] total chunks: {len(texts)}")

        model = SentenceTransformer(EMBED_MODEL_NAME, cache_folder="./.cache")
        print("[KB] embedding...")
        embeds = model.encode(texts, show_progress_bar=True).astype("float32")

        print("[KB] building FAISS index...")
        index = faiss.IndexFlatL2(embeds.shape[1])
        index.add(embeds)
        faiss.write_index(index, INDEX_PATH)
        json.dump(meta, open(CHUNKS_PATH, "w"), indent=2)

        print("[KB] done.")
        return cls()

    def search(self, text, k=5):
        emb = self.model.encode([text]).astype("float32")
        D, I = self.index.search(emb, k)
        results = []
        for d, idx in zip(D[0], I[0]):
            results.append({
                "score": float(d),
                "text": self.chunks[idx]["text"],
                "source": self.chunks[idx]["source"]
            })
        return results
