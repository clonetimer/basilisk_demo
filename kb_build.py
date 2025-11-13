# kb_build.py —— 一次性构建向量库 + 自动构建规则库

from rag_engine import RAGEngine
from rule_extractor import scan_classes, generate_rules
from config import DOCS_DIR, RULES_PATH

import json
import os

if __name__ == "__main__":
    print("=== Building Basilisk RAG KB ===")

    # (1) build FAISS knowledge base
    RAGEngine.build_from_corpus()

    # (2) build rules
    print("[RULE] Extracting rules...")
    classes = scan_classes(DOCS_DIR)
    rules = generate_rules(classes)
    os.makedirs(os.path.dirname(RULES_PATH), exist_ok=True)
    json.dump(rules, open(RULES_PATH, "w"), indent=2)
    print("[RULE] Saved:", RULES_PATH)

    print("=== Done ===")
