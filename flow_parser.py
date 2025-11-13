import re
import networkx as nx

NODE_PATTERN = re.compile(r"(\w+)=>(\w+):([^\n]+)")
EDGE_PATTERN = re.compile(r"(\w+)->(\w+)")

def parse_flowchart(text):
    nodes = {}
    for name, kind, desc in NODE_PATTERN.findall(text):
        nodes[name] = {"type": kind, "text": desc}

    edges = EDGE_PATTERN.findall(text)

    G = nx.DiGraph()
    for n, info in nodes.items():
        G.add_node(n, **info)
    for a, b in edges:
        G.add_edge(a, b)

    try:
        order = list(nx.topological_sort(G))
    except:
        order = list(nodes.keys())

    return [{"id": nid, "text": nodes[nid]["text"]} for nid in order]
