import os
import ast
import json
from config import DOCS_DIR

OUTPUT = "auto_modules.json"


def scan_basilisk_modules(root):
    modules = {}
    for r, _, fs in os.walk(root):
        for f in fs:
            if f.endswith(".py"):
                path = os.path.join(r, f)
                try:
                    tree = ast.parse(open(path).read())
                except:
                    continue

                classes = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        classes.append(node.name)

                if classes:
                    modules[path] = classes

    return modules


if __name__ == "__main__":
    modules = scan_basilisk_modules(DOCS_DIR)
    json.dump(modules, open(OUTPUT, "w"), indent=2)
    print("saved:", OUTPUT)
