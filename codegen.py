# ---------------------------------------------------------------
# codegen.py — 改进版：优先匹配自然语言，再匹配 RULES.json
# ---------------------------------------------------------------

import json
from config import RULES_PATH

# 自动规则（来自 rule_extractor）
RULES = json.load(open(RULES_PATH, "r", encoding="utf-8"))

# -----------------------------------------
# 1) 自然语言 → 模块类型 的人工 mapping（关键新增）
# -----------------------------------------
MANUAL_RULES = {
    "init spacecraft": "spacecraft",
    "spacecraft": "spacecraft",

    "add gravity": "gravity",
    "gravity": "gravity",

    "run simulation": "simulation",
    "start": "noop",
    "end": "noop",

    "add rw": "reactionwheel",
    "reaction wheel": "reactionwheel",

    "add thruster": "thruster",
    "thruster": "thruster",

    "add css": "coarsesunsensor",
    # "add fss": "finesunsensor",

    "simplenav": "simplenav",
    "nav": "simplenav",
    "add nav": "simplenav",

    "orbit": "orbit",
    "add orbit": "orbit",
}

# -----------------------------------------
# 为手工规则提供模板（可扩展）
# -----------------------------------------
MANUAL_TEMPLATES = {
    "spacecraft": [
        "scObject = spacecraft.Spacecraft()",
        "scSim.AddModelToTask(simTaskName, scObject)"
    ],
    "gravity": [
        "gravFactory = simIncludeGravBody.gravBodyFactory()",
        "earth = gravFactory.createEarth()",
        "scObject.gravField.gravBodies = gravFactory.gravBodies"
    ],
    "reactionwheel": [
        "rw = reactionWheelStateEffector.ReactionWheelStateEffector()",
        "scObject.addDynamicEffector(rw)"
    ],
    # "rotationwheel": [],      # from RULES
    "thruster": [],           # fallback to RULES
    "simplenav": [],          # fallback
    "orbit": [],              # fallback
    "noop": [],               # start/end
    "simulation": []          # execution handled globally
}

# -----------------------------------------
# 文本匹配工具
# -----------------------------------------
def try_manual_rule(text):
    t = text.lower().strip()
    for k, v in MANUAL_RULES.items():
        if k in t:
            return v
    return None


def try_auto_rule(text):
    low = text.lower()
    for key, info in RULES.items():
        for kw in info["keywords"]:
            if kw in low:
                return key
    return None


# -----------------------------------------
# 最终生成代码
# -----------------------------------------
# from Basilisk.simulation import thrusterDynamicEffector, coarseSunSensor, fineSunSensor
IMPORTS = """
from Basilisk.utilities import SimulationBaseClass
from Basilisk.simulation import spacecraft
from Basilisk.simulation import thrusterDynamicEffector, coarseSunSensor
from Basilisk.simulation import reactionWheelStateEffector
from Basilisk.simulation import simpleNav
from Basilisk.utilities import orbitalMotion, simIncludeGravBody, macros
"""


def assemble_script(tasks):
    lines = [
        IMPORTS,
        "",
        "def main():",
        "    simBase = SimulationBaseClass.SimBaseClass()",
        "    simTaskName = 'simTask'",
        "    proc = simBase.CreateNewProcess('simProc')",
        "    task = simBase.CreateNewTask(simTaskName, int(1e9))",
        "    proc.addTask(task)",
        ""
    ]

    for t in tasks:
        desc = t["text"]
        lines.append(f"    # Step: {desc}")

        # (1) 优先自然语言
        manual = try_manual_rule(desc)
        if manual:
            template = MANUAL_TEMPLATES.get(manual, None)
            if template:
                for c in template:
                    lines.append("    " + c)
                lines.append("")
                continue
            # else fall back to auto rule

        # (2) 自动 RULES.json
        auto_key = try_auto_rule(desc)
        if auto_key:
            for c in RULES[auto_key]["code"]:
                lines.append("    " + c)
            lines.append("")
            continue

        # (3) Fallback
        lines.append("    # TODO: no matching rule")
        lines.append("")

    # finishing
    lines += [
        "    simBase.ConfigureStopTime(int(10e9))",
        "    simBase.InitializeSimulation()",
        "    simBase.ExecuteSimulation()",
        "",
        "if __name__ == '__main__': main()"
    ]

    return "\n".join(lines)
