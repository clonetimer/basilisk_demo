# ============================================================
# rule_extractor.py —— Basilisk 专用自动模块规则提取器（最终版）
# ============================================================

import os
import ast
import json
from config import DOCS_DIR, RULES_PATH


# -----------------------------------------------
# 0) 限定扫描路径：只扫描真正的仿真模块，而不是 messages/config
# -----------------------------------------------
VALID_DIRS = [
    "architecture",
    "ExternalModels"
    "simulation",
    "fswAlgorithms",
    "utilities",
    "dynamics",
    "sensors",
    "effector"
]


# -----------------------------------------------
# 1) 判断是否是可用的 Basilisk 模块类
# -----------------------------------------------
def is_valid_class(clsname: str) -> bool:
    name = clsname.lower()
    bad = ["payload", "msg", "config", "data", "interface", "record"]

    if any(b in name for b in bad):
        return False

    # exclude abstract classes
    if name in ["modeltemplate"]:
        return False

    return True


# -----------------------------------------------
# 2) 扫描 Basilisk 目录下所有可用类（过滤无关类）
# -----------------------------------------------
def scan_classes(root):
    class_map = {}

    for r, _, fs in os.walk(root):
        # 只扫描包含 VALID_DIRS 的路径
        path_norm = r.replace("\\", "/").lower()
        if not any(v in path_norm for v in VALID_DIRS):
            continue

        for f in fs:
            if not f.endswith(".py"):
                continue

            full_path = os.path.join(r, f)
            try:
                code = open(full_path, "r", encoding="utf-8").read()
            except:
                continue

            try:
                tree = ast.parse(code)
            except:
                continue

            valid_classes = []

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    if is_valid_class(node.name):
                        valid_classes.append(node.name)

            if valid_classes:
                class_map[full_path] = valid_classes

    return class_map


# -----------------------------------------------
# 3) 规范化模块路径：将 “.../simulation/foo/bar.py” 转为 import 的 module 名
# -----------------------------------------------
def path_to_module(path):
    # 先相对化路径
    rel = os.path.relpath(path, DOCS_DIR)
    rel = rel.replace("\\", "/")  # Windows
    # 去掉 .py
    rel = rel.replace(".py", "")
    # 转为 Python module 格式
    mod = rel.replace("/", ".")
    return mod


# -----------------------------------------------
# 4) 按模块类型生成关键词（匹配 Flowchart 文本）
# -----------------------------------------------
def expand_keywords(cls):
    name = cls.lower()
    kw = [name]

    if "spacecraft" in name:
        kw += ["spacecraft", "init spacecraft"]

    if "grav" in name:
        kw += ["gravity", "earth gravity"]

    if "rw" in name:
        kw += ["rw", "reaction wheel"]

    if "thruster" in name or "dynamiceffector" in name:
        kw += ["thruster", "thr"]

    if "sensor" in name:
        kw += ["sensor", "css", "fss"]

    if "nav" in name:
        kw += ["nav", "navigation", "simplenav"]

    if "element" in name or "orbit" in name:
        kw += ["orbit", "kepler"]

    if "pressure" in name:
        kw += ["srp", "solar radiation"]

    if "mag" in name:
        kw += ["magnetic", "mag field"]

    return list(set(kw))


# -----------------------------------------------
# 5) 为各类模块生成模板（真正可运行）
# -----------------------------------------------
def generate_code_template(cls, module_name):
    # 变量名用模块名最后一段
    var = module_name.split(".")[-1]
    lname = cls.lower()

    # ---------------- Spacecraft ----------------
    if "spacecraft" in lname:
        return [
            f"scObject = {module_name}.{cls}()",
            "scSim.AddModelToTask(simTaskName, scObject)"
        ]

    # ---------------- Gravity ----------------
    if "grav" in lname and "factory" in lname:
        return [
            "gravFactory = simIncludeGravBody.gravBodyFactory()",
            "planet = gravFactory.createEarth()",
            "gravFactory.addBodiesTo(scObject)",
            "mu = planet.mu"
        ]

    # ---------------- RW ----------------
    if "rw" in lname and "effector" in lname:
        return [
            f"rw = {module_name}.{cls}()",
            "scObject.addDynamicEffector(rw)"
        ]

    # ---------------- Thruster ----------------
    if "thruster" in lname or "dynamiceffector" in lname:
        return [
            f"thr = {module_name}.{cls}()",
            "scObject.addDynamicEffector(thr)"
        ]

    # ---------------- Sensors (CSS / FSS) ----------------
    if "sensor" in lname:
        return [
            f"sens = {module_name}.{cls}()",
            "scObject.addSensor(sens)"
        ]

    # ---------------- Navigation (SimpleNav / NavEKF) ----------------
    if "nav" in lname:
        return [
            f"nav = {module_name}.{cls}()",
            "scSim.AddModelToTask(simTaskName, nav)"
        ]

    # ---------------- Orbit (ClassicElements) ----------------
    if "element" in lname or "orbit" in lname:
        return [
            f"oe = {module_name}.{cls}()",
            "oe.a = 7000e3",
            "oe.e = 0.0",
            "oe.i = 0.0",
            "oe.Omega = 48.2 * macros.D2R",
            "oe.omega = 347.8 * macros.D2R",
            "oe.f = 85.3 * macros.D2R",
            "rN, vN = orbitalMotion.elem2rv(mu, oe)",
            "oe = orbitalMotion.rv2elem(mu, rN, vN)",
            "scObject.hub.r_CN_NInit = rN",
            "scObject.hub.v_CN_NInit = vN"
        ]

    # ---------------- Unknown type ----------------
    return [f"# TODO: No auto template for {cls}"]


# -----------------------------------------------
# 6) 生成 rules.json
# -----------------------------------------------
def generate_rules(class_map):
    rules = {}

    for path, classes in class_map.items():
        module = path_to_module(path)
        for cls in classes:
            key = cls.lower()
            rules[key] = {
                "class": cls,
                "module": module,
                "keywords": expand_keywords(cls),
                "code": generate_code_template(cls, module)
            }

    return rules


# -----------------------------------------------
# 7) CLI 用
# -----------------------------------------------
if __name__ == "__main__":
    class_map = scan_classes(DOCS_DIR)
    rules = generate_rules(class_map)
    os.makedirs(os.path.dirname(RULES_PATH), exist_ok=True)
    json.dump(rules, open(RULES_PATH, "w"), indent=2)
    print("Saved:", RULES_PATH)
