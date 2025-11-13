# example_to_flow.py

import ast
import os


def extract_actions_from_py(path):
    code = open(path).read()
    tree = ast.parse(code)

    actions = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            text = ast.unparse(node)
            actions.append(("assign", text))

        if isinstance(node, ast.Call):
            call = ast.unparse(node)
            actions.append(("call", call))

    return actions


def actions_to_flow(actions):
    flow = []
    flow.append("st=>start: Start")

    flow_nodes = []
    idx = 1
    for typ, act in actions:
        label = act.replace("\n", " ")[:40]
        flow_nodes.append(f"op{idx}=>operation: {label}")
        idx += 1

    flow.append("\n".join(flow_nodes))
    flow.append("e=>end: End\n")

    # 连接关系
    flow.append("st")
    for i in range(1, len(flow_nodes) + 1):
        flow.append(f"->op{i}")
    flow.append("->e")

    return "\n".join(flow)


def generate_flow_from_example(py_path, out_path):
    actions = extract_actions_from_py(py_path)
    flow_txt = actions_to_flow(actions)
    open(out_path, "w").write(flow_txt)
    print("Flowchart generated:", out_path)


if __name__ == "__main__":
    py_path = "./data/docs/basilisk_examples/ScenarioAttitudeControl.py"
    out_path = py_path.replace(".py", ".flow")
    generate_flow_from_example(py_path, out_path)
