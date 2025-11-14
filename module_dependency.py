# module_dependency.py

import networkx as nx

# 模块关键节点映射（匹配 codegen 中的模块 key）
MODULE_KEYS = [
    "spacecraft",
    "gravity",
    "reactionwheel",
    "thruster",
    "css",
    "fss",
    "simplenav",
    "orbit",
    "srp",
    "magfield"
]

# 模块顺序依赖图：A → B 表示 A 必须在 B 之前
DEPENDENCIES = {
    "spacecraft": [],
    "gravity": ["spacecraft"],
    "orbit": ["spacecraft"],
    "reactionwheel": ["spacecraft"],
    "thruster": ["spacecraft"],
    "css": ["spacecraft"],
    "fss": ["spacecraft"],
    "simplenav": ["spacecraft"],
    "srp": ["spacecraft"],
    "magfield": ["spacecraft"]
}


def build_dependency_graph():
    G = nx.DiGraph()
    for m in MODULE_KEYS:
        G.add_node(m)
    for m, deps in DEPENDENCIES.items():
        for d in deps:
            G.add_edge(d, m)
    return G


def reorder_tasks(task_list):
    """
    将解析出的任务列表（包含 text 和 module_key）重排序为符合依赖顺序
    返回排序后的任务列表
    """
    G = build_dependency_graph()

    matched = []
    for t in task_list:
        key = t.get("module_key")
        if key in MODULE_KEYS:
            matched.append((key, t))
        else:
            matched.append((None, t))

    selected_nodes = [k for k, _ in matched if k]
    sub = G.subgraph(selected_nodes)
    if len(sub.nodes) > 0:
        topo = list(nx.topological_sort(sub))
    else:
        topo = []

    reordered = []
    for k in topo:
        for mk, t in matched:
            if mk == k:
                reordered.append(t)

    for mk, t in matched:
        if mk not in topo:
            reordered.append(t)

    return reordered


if __name__ == "__main__":
    sample = [
        {"text": "Add Thruster set", "module_key": "thruster"},
        {"text": "Init spacecraft", "module_key": "spacecraft"},
        {"text": "Add Gravity model", "module_key": "gravity"}
    ]
    ordered = reorder_tasks(sample)
    print("Reordered task list:")
    for t in ordered:
        print("  ", t["text"])
