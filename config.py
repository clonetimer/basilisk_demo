import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ========= 文档目录（你放 Basilisk 源码/文档/examples）=========
DOCS_DIR = os.path.join(BASE_DIR, "data", "docs")

# ========= 知识库目录 =========
KB_DIR = os.path.join(BASE_DIR, "kb")
CHUNKS_PATH = os.path.join(KB_DIR, "bsk_chunks.json")
INDEX_PATH = os.path.join(KB_DIR, "bsk_index.faiss")
RULES_PATH = os.path.join(KB_DIR, "rules.json")

# ========= 向量模型 =========
EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# ========= 输入输出 =========
EXAMPLE_FLOW = os.path.join(BASE_DIR, "examples", "simple.flow")
OUTPUT_SCRIPT = os.path.join(BASE_DIR, "auto_basilisk_sim.py")
