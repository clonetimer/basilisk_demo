# codegen.py — 基于《代码切片.md》的手工规则版
# ---------------------------------------------------
# 约定：
# - 输入：flow_parser 解析得到的 tasks（list[{"text": str, ...}])
# - 输出：一个完整的 Basilisk 仿真脚本字符串
# - 不依赖 LLM / RULES.json，仅靠手工规则 + 代码片段库
# - 只支持英文 Flowchart 节点（lowercase 匹配）

import re
from typing import List, Dict
from module_dependency import reorder_tasks

# ============================================================
# 1. 关键字 → 模块类型映射（英文，只匹配 .lower() 后的子串）
# ============================================================

KEYWORDS_MAP = {
    # 核心
    "spacecraft": ["init spacecraft", "create spacecraft", "spacecraft"],
    "gravity": ["add earth gravity", "add gravity", "gravity model"],
    "orbit": ["set orbit", "set circular orbit", "orbit"],
    "srp": ["add srp", "solar radiation"],
    "atmosphere": ["add atmosphere", "add drag", "exponential atmosphere"],

    # 执行机构
    "reactionwheel": ["add reaction wheel", "add rw", "reaction wheel", "rw"],
    "thruster": ["add thruster", "thruster set", "add thruster set"],

    # 传感器
    "css": ["add css", "add sun sensor", "coarse sun sensor"],
    # "fss": ["add fss", "fine sun sensor"],
    "imu": ["add imu"],
    "camera": ["add camera"],
    "tam": ["add tam", "add magnetometer"],

    # 导航
    "simplenav": ["add simplenav", "add simple nav", "add navigation"],

    # 数据记录 & 可视化
    "logging": ["enable logging", "record states", "add logger"],
    "plot": ["plot states", "plot results", "plot position"],

    # 仿真执行
    "run": ["run simulation", "execute simulation", "start simulation"]
}


def match_module(text: str) -> str:
    low = text.lower()
    for key, patterns in KEYWORDS_MAP.items():
        for p in patterns:
            if p in low:
                return key
    return ""


def parse_run_time(text: str, default_sec: float = 10.0) -> float:
    m = re.search(r"(\d+\.?\d*)\s*(s|sec|secs|second|seconds)?", text.lower())
    if m:
        return float(m.group(1))
    return default_sec


# ============================================================
# 2. 代码模板（全部来自《代码切片.md》稍作裁剪、规范化）
# ============================================================

TEMPLATE_IMPORTS = """\
import os
import sys
import numpy as np
import matplotlib.pyplot as plt

from Basilisk.utilities import SimulationBaseClass, macros, orbitalMotion, simIncludeGravBody, simIncludeRW, simIncludeThruster
from Basilisk.simulation import spacecraft
from Basilisk.simulation import radiationPressure, exponentialAtmosphere
from Basilisk.simulation import reactionWheelStateEffector, thrusterDynamicEffector
from Basilisk.simulation import coarseSunSensor, imuSensor, camera, tamSensor
from Basilisk.simulation import simpleNav
"""

TEMPLATE_SIM_SETUP = [
    "# === Simulation Core ===",
    "scSim = SimulationBaseClass.SimBaseClass()",
    "scSim.SetProgressBar(True)",
    "",
    "simTaskName = 'simTask'",
    "simProcessName = 'simProcess'",
    "",
    "dynProcess = scSim.CreateNewProcess(simProcessName)",
    "simulationTimeStep = macros.sec2nano(10.0)  # 10 s step (example)",
    "dynProcess.addTask(scSim.CreateNewTask(simTaskName, simulationTimeStep))",
    "",
    "# Logging sampling time",
    "samplingTime = macros.sec2nano(1.0)",
    ""
]

TEMPLATE_SPACECRAFT = [
    "# === Spacecraft ===",
    "scObject = spacecraft.Spacecraft()",
    "scObject.ModelTag = 'bsk-Sat'",
    "",
    "# Mass properties",
    "scObject.hub.mHub = 750.0",
    "I = [[900.0, 0.0, 0.0],",
    "     [0.0, 800.0, 0.0],",
    "     [0.0, 0.0, 600.0]]",
    "scObject.hub.IHubPntBc_B = I",
    "",
    "# Default initial state (can be overwritten by Orbit block)",
    "scObject.hub.r_CN_NInit = [[-6000000.0], [0.0], [0.0]]",
    "scObject.hub.v_CN_NInit = [[0.0], [-7500.0], [0.0]]",
    "scObject.hub.sigma_BNInit = [[0.1], [0.2], [-0.3]]",
    "scObject.hub.omega_BN_BInit = [[0.001], [-0.01], [0.03]]",
    "",
    "scSim.AddModelToTask(simTaskName, scObject)",
    ""
]

TEMPLATE_GRAVITY = [
    "# === Earth Gravity ===",
    "gravFactory = simIncludeGravBody.gravBodyFactory()",
    "earth = gravFactory.createEarth()",
    "earth.isCentralBody = True",
    "mu = earth.mu",
    "# Example: enable J2-only spherical harmonics model (path needs adjustment)",
    "# earth.useSphericalHarmonicsGravityModel(bskPath + '/supportData/LocalGravData/GGM03S-J2-only.txt', 2)",
    "",
    "gravFactory.addBodiesTo(scObject)",
    ""
]

TEMPLATE_ORBIT = [
    "# === Initial Orbit (circular, a=7000 km) ===",
    "oe = orbitalMotion.ClassicElements()",
    "oe.a = 7000e3",          # semi-major axis [m]
    "oe.e = 0.0",             # eccentricity
    "oe.i = 0.0",             # inclination [rad]",
    "oe.Omega = 48.2 * macros.D2R",
    "oe.omega = 347.8 * macros.D2R",
    "oe.f = 85.3 * macros.D2R",
    "rN, vN = orbitalMotion.elem2rv(mu, oe)",
    "oe = orbitalMotion.rv2elem(mu, rN, vN)",
    "scObject.hub.r_CN_NInit = rN",
    "scObject.hub.v_CN_NInit = vN",
    ""
]

TEMPLATE_SRP = [
    "# === Solar Radiation Pressure ===",
    "srp = radiationPressure.RadiationPressure()",
    "srp.ModelTag = 'Solar_Radiation_Pressure'",
    "# srp.sunPositionInMsg.subscribeTo(spiceObject.sunStateOutMsg)  # if SPICE is used",
    "srp.spacecraftPositionInMsg.subscribeTo(scObject.scStateOutMsg)",
    "srp.nominalFlux = 1367.0  # W/m^2",
    "scSim.AddModelToTask(simTaskName, srp)",
    ""
]

TEMPLATE_ATMOSPHERE = [
    "# === Exponential Atmosphere ===",
    "atmoModel = exponentialAtmosphere.ExponentialAtmosphere()",
    "atmoModel.ModelTag = 'Earth_Atmosphere'",
    "atmoModel.baseDensity = 1.225  # kg/m^3",
    "atmoModel.scaleHeight = 8500.0  # m",
    "atmoModel.planetRadius = 6371000.0  # m",
    "atmoModel.atmoDamping = 0.3",
    "atmoModel.spacecraftPositionInMsg.subscribeTo(scObject.scStateOutMsg)",
    "scSim.AddModelToTask(simTaskName, atmoModel)",
    ""
]

TEMPLATE_RW = [
    "# === Reaction Wheels ===",
    "rwStateEffector = reactionWheelStateEffector.ReactionWheelStateEffector()",
    "rwStateEffector.ModelTag = 'ReactionWheels'",
    "scSim.AddModelToTask(simTaskName, rwStateEffector)",
    "",
    "rwFactory = simIncludeRW.rwFactory()",
    "rwFactory.create('Honeywell_HR16', [1, 0, 0], maxMomentum=50.0)",
    "rwFactory.create('Honeywell_HR16', [0, 1, 0], maxMomentum=50.0)",
    "rwFactory.create('Honeywell_HR16', [0, 0, 1], maxMomentum=50.0)",
    "rwFactory.addToSpacecraft(scObject.ModelTag, rwStateEffector, scObject)",
    ""
]

TEMPLATE_THRUSTER = [
    "# === Thruster Set ===",
    "thrusterSet = thrusterDynamicEffector.ThrusterDynamicEffector()",
    "thrusterSet.ModelTag = 'Thrusters'",
    "scSim.AddModelToTask(simTaskName, thrusterSet)",
    "",
    "thrFactory = simIncludeThruster.thrusterFactory()",
    "thrFactory.create('Pulsed Plasma Thruster', [1.0, 0.0, 0.0], [0.5, 0.5, 0.5])",
    "thrFactory.create('Pulsed Plasma Thruster', [-1.0, 0.0, 0.0], [0.5, 0.5, -0.5])",
    "thrFactory.addToSpacecraft(thrusterSet, scObject)",
    ""
]

TEMPLATE_CSS = [
    "# === Coarse Sun Sensor (CSS) ===",
    "cssObj = coarseSunSensor.CoarseSunSensor()",
    "cssObj.ModelTag = 'CSS'",
    "cssObj.nHat_B = [0.0, 0.0, 1.0]",
    "cssObj.fieldOfView = 60.0",
    "cssObj.scaleFactor = 10.0",
    "cssObj.fovHalfAngle = 30.0",
    "scSim.AddModelToTask(simTaskName, cssObj)",
    ""
]

'''
TEMPLATE_FSS = [
    "# === Fine Sun Sensor (placeholder using camera) ===",
    "fss = camera.Camera()",
    "fss.ModelTag = 'FSS'",
    "scSim.AddModelToTask(simTaskName, fss)",
    ""
]
'''

TEMPLATE_IMU = [
    "# === IMU Sensor ===",
    "imu = imuSensor.ImuSensor()",
    "imu.ModelTag = 'IMU_Sensor'",
    "scSim.AddModelToTask(simTaskName, imu)",
    "imu.rw = [[0.001], [0.001], [0.001]]  # random walk (example)",
    ""
]

TEMPLATE_CAMERA = [
    "# === Camera ===",
    "cam = camera.Camera()",
    "cam.ModelTag = 'Camera'",
    "cam.focalLength = 0.05  # m",
    "cam.resolution = [1024, 1024]",
    "cam.fieldOfView = 60.0  # deg",
    "scSim.AddModelToTask(simTaskName, cam)",
    ""
]

TEMPLATE_TAM = [
    "# === Three-Axis Magnetometer (TAM) ===",
    "tam = tamSensor.TamSensor()",
    "tam.ModelTag = 'TAM_Sensor'",
    "scSim.AddModelToTask(simTaskName, tam)",
    ""
]

TEMPLATE_SIMPLENAV = [
    "# === SimpleNav ===",
    "sNavObject = simpleNav.SimpleNav()",
    "sNavObject.ModelTag = 'SimpleNavigation'",
    "scSim.AddModelToTask(simTaskName, sNavObject)",
    "sNavObject.scStateInMsg.subscribeTo(scObject.scStateOutMsg)",
    ""
]

TEMPLATE_LOGGING = [
    "# === State Logging ===",
    "dataLog = scObject.scStateOutMsg.recorder(samplingTime)",
    "scSim.AddModelToTask(simTaskName, dataLog)",
    ""
]

TEMPLATE_PLOT = [
    "# === Plot Position ===",
    "timeAxis = dataLog.times() * macros.NANO2SEC",
    "posData = dataLog.r_BN_N",
    "",
    "plt.figure(1)",
    "for idx in range(3):",
    "    plt.plot(timeAxis, posData[:, idx])",
    "plt.xlabel('Time (s)')",
    "plt.ylabel('Position (m)')",
    "plt.legend(['x', 'y', 'z'])",
    "plt.grid(True)",
    "plt.savefig('position_xyz.png')",
    ""
]


# ------------------------------------------------
# 3. 主函数：由 Flowchart 任务 → Python 脚本字符串
# ------------------------------------------------
def assemble_script(flow_tasks: List[Dict]) -> str:
    """
    flow_tasks: [{ "id": ..., "text": ... }]
    返回自动生成的 Basilisk Python 仿真脚本源码字符串
    """

    # 1) 为每个任务匹配模块 key
    tasks_with_key = []
    for t in flow_tasks:
        key = match_module(t["text"])
        t2 = {
            "id": t.get("id"),
            "text": t["text"],
            "module_key": key
        }
        tasks_with_key.append(t2)

    # 2) 按模块依赖关系重排
    ordered = reorder_tasks(tasks_with_key)

    # 3) 开始拼脚本
    lines: List[str] = []

    lines.append(TEMPLATE_IMPORTS)
    lines.append("")
    lines.append("")
    lines.append("def main():")
    lines.append("    # === Auto Generated Basilisk Script ===")
    lines.append("")
    for L in TEMPLATE_SIM_SETUP:
        lines.append("    " + L)
    lines.append("")

    used = {k: False for k in KEYWORDS_MAP.keys()}
    run_time = 10.0

    for t in ordered:
        desc = t["text"]
        key = t["module_key"]

        lines.append(f"    # Flowchart Step: {desc}")

        if not key:
            lines.append("    # (Unmatched step)")
            lines.append("")
            continue

        # 单次模块：重复出现就跳过
        if used.get(key, False) and key not in ["logging", "plot", "run"]:
            lines.append("    # (module already added)")
            lines.append("")
            continue

        if key == "spacecraft":
            for L in TEMPLATE_SPACECRAFT:
                lines.append("    " + L)

        elif key == "gravity":
            for L in TEMPLATE_GRAVITY:
                lines.append("    " + L)

        elif key == "orbit":
            for L in TEMPLATE_ORBIT:
                lines.append("    " + L)

        elif key == "reactionwheel":
            for L in TEMPLATE_RW:
                lines.append("    " + L)

        elif key == "thruster":
            for L in TEMPLATE_THRUSTER:
                lines.append("    " + L)

        elif key == "css":
            for L in TEMPLATE_CSS:
                lines.append("    " + L)

        elif key == "fss":
            for L in TEMPLATE_FSS:
                lines.append("    " + L)

        elif key == "simplenav":
            for L in TEMPLATE_SIMPLENAV:
                lines.append("    " + L)

        elif key == "srp":
            for L in TEMPLATE_SRP:
                lines.append("    " + L)

        elif key == "atmosphere":
            for L in TEMPLATE_ATMOSPHERE:
                lines.append("    " + L)

        elif key == "logging":
            if not used["logging"]:
                for L in TEMPLATE_LOGGING:
                    lines.append("    " + L)

        elif key == "plot":
            used["plot"] = True
            lines.append("    # (plot will be added after simulation)")
            lines.append("")

        elif key == "run":
            run_time = parse_run_time(desc, default_sec=10.0)
            used["run"] = True
            lines.append(f"    # parsed run_time = {run_time} s")
            lines.append("")

        used[key] = True
        lines.append("")

    # 4) 仿真执行
    lines.append("    # === Run Simulation ===")
    lines.append(f"    simTime = macros.sec2nano({run_time})")
    lines.append("    scSim.ConfigureStopTime(simTime)")
    lines.append("    scSim.InitializeSimulation()")
    lines.append("    scSim.ExecuteSimulation()")
    lines.append("")

    # 5) 如启用了 logging & plot，则生成绘图代码
    if used.get("logging", False) and used.get("plot", False):
        for L in TEMPLATE_PLOT:
            lines.append("    " + L)

    lines.append("")
    lines.append("if __name__ == '__main__':")
    lines.append("    main()")
    lines.append("")

    return "\n".join(lines)