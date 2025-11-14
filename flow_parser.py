import re
import networkx as nx

# 节点定义：st=>start: Start
NODE_PATTERN = re.compile(r"(\w+)=>(\w+):([^\n]+)")

# 边定义两种形式：
# 1) 链式：st->op1->op2->e
# 2) 单条：st->op1
EDGE_CHAIN_PATTERN = re.compile(r'(\w+(?:->\w+)+)')
EDGE_SIMPLE_PATTERN = re.compile(r'(\w+)->(\w+)')


def _normalize_chain_item(item):
    """re.findall 可能返回字符串，也可能返回元组，这里统一转成字符串"""
    if isinstance(item, tuple):
        # 一般来说 tuple[0] 就是整个匹配串
        return item[0]
    return item


def parse_edges_improved(text: str):
    """
    解析 flowchart.js 中的连线：
    - 支持 st->op1->op2->e 这种链式
    - 也支持散落的 a->b
    """
    edges = set()

    # 1) 先解析链式：st->op1->op2->e
    for chain in EDGE_CHAIN_PATTERN.findall(text):
        chain_str = _normalize_chain_item(chain)
        parts = chain_str.split("->")
        for i in range(len(parts) - 1):
            a, b = parts[i].strip(), parts[i + 1].strip()
            if a and b:
                edges.add((a, b))

    # 2) 再解析所有单条 a->b，补充可能遗漏的边
    for a, b in EDGE_SIMPLE_PATTERN.findall(text):
        a, b = a.strip(), b.strip()
        if a and b:
            edges.add((a, b))

    return list(edges)


def parse_flowchart(text: str):
    """
    输入：flowchart.js 文本
    输出：
    {
      "ordered_tasks": [
        {"id": "op1", "text": "Init spacecraft"},
        ...
      ]
    }
    """
    # 1) 解析节点
    nodes = {}
    for name, kind, desc in NODE_PATTERN.findall(text):
        nodes[name] = {
            "type": kind,
            "text": desc.strip()
        }

    # 2) 解析边
    edges = parse_edges_improved(text)

    # 3) 拓扑排序
    G = nx.DiGraph()
    for n, info in nodes.items():
        G.add_node(n, **info)
    for a, b in edges:
        if a in nodes and b in nodes:
            G.add_edge(a, b)

    try:
        order = list(nx.topological_sort(G))
    except Exception:
        # 有环或者图不完整时，就按定义顺序
        order = list(nodes.keys())

    return {
        "ordered_tasks": [
            {"id": nid, "text": nodes[nid]["text"]}
            for nid in order
        ]
    }


if __name__ == "__main__":
    demo = """
    st=>start: Start
    op1=>operation: Init spacecraft
    op2=>operation: Add Earth gravity
    op3=>operation: Run simulation 100s
    e=>end: End

    st->op1->op2->op3->e
    """
    res = parse_flowchart(demo)
    print(res["ordered_tasks"])
