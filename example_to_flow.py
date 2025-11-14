# example_to_flow.py — 方案 A 版本
# 从 Basilisk 示例 Python 文件中提取模块类型 → 生成英文 Flowchart.js

import ast
import os


# 1) 代码行 → 模块 key（需与 module_dependency.MODULE_KEYS / codegen.KEYWORDS_MAP 对齐）
CLASS_KEYWORDS = {
    "spacecraft": ["spacecraft."],
    "gravity": ["gravbodyfactory", "createearth"],
    "orbit": ["classicelements", "elem2rv"],
    "reactionwheel": ["reactionwheelstateeffector"],
    "thruster": ["thrusterdynamiceffector"],
    "css": ["coarse sun sensor", "coarsesunsensor"],
    "fss": ["finesunsensor"],
    "simplenav": ["simplenav"],
    "srp": ["radiationpressure"],
    "magfield": ["magneticfield"],
    "atmosphere": ["exponentialatmosphere", "msisatmosphere"],
}


MODULE_LABELS = {
    "spacecraft": "Init spacecraft",
    "gravity": "Add Earth gravity",
    "orbit": "Set circular orbit",
    "reactionwheel": "Add reaction wheel",
    "thruster": "Add thruster set",
    "css": "Add CSS",
    "fss": "Add FSS",
    "simplenav": "Add SimpleNav",
    "srp": "Add SRP",
    "magfield": "Add magnetic field",
    "atmosphere": "Add atmosphere",
}


def extract_actions(py_path: str):
    code = open(py_path, "r", encoding="utf-8").read()
    try:
        tree = ast.parse(code)
    except SyntaxError:
        print(f"[WARN] Cannot parse {py_path}")
        return []

    actions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            actions.append(ast.unparse(node))
        elif isinstance(node, ast.Assign):
            actions.append(ast.unparse(node))
    return actions


def classify_action(line: str):
    low = line.lower()
    for mod, kws in CLASS_KEYWORDS.items():
        for kw in kws:
            if kw in low:
                return mod
    return None


def reduce_modules(actions):
    modules = []
    seen = set()
    for line in actions:
        m = classify_action(line)
        if m and m not in seen:
            seen.add(m)
            modules.append(m)
    return modules


def build_flowchart(modules):
    lines = ["st=>start: Start"]

    nodes = []
    for i, m in enumerate(modules, start=1):
        label = MODULE_LABELS.get(m, m)
        nodes.append(f"op{i}=>operation: {label}")
    lines.extend(nodes)

    lines.append("e=>end: End\n")

    seq = ["st"]
    for i in range(1, len(modules) + 1):
        seq.append(f"op{i}")
    seq.append("e")
    lines.append("->".join(seq))

    return "\n".join(lines)


def generate_flow(example_py_path: str, out_flow_path: str):
    actions = extract_actions(example_py_path)
    modules = reduce_modules(actions)
    flow_txt = build_flowchart(modules)

    with open(out_flow_path, "w", encoding="utf-8") as f:
        f.write(flow_txt)

    print(f"[OK] Generated flowchart: {out_flow_path}")
    print(f"     Modules detected: {modules}")


if __name__ == "__main__":
    # 示例：从某个 Basilisk example 生成 .flow
    example = "./data/docs/to_flow/scenarioBasicOrbit.py"
    out = example.replace(".py", ".flow")
    generate_flow(example, out)
