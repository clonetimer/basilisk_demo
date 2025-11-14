# main.py — 方案 A 版本
# 入口：Flowchart.js → auto_basilisk_sim.py

from config import OUTPUT_SCRIPT
from flow_parser import parse_flowchart
from codegen import assemble_script


def main(flow_path: str):
    print(f"[Main] 读取流程图: {flow_path}")

    with open(flow_path, "r", encoding="utf-8") as f:
        flow_text = f.read()

    parsed = parse_flowchart(flow_text)
    tasks = parsed["ordered_tasks"]
    print(f"[Main] Flowchart 解析得到 {len(tasks)} 个步骤")

    print("[Main] 生成 Basilisk 仿真脚本...")
    script = assemble_script(tasks)

    with open(OUTPUT_SCRIPT, "w", encoding="utf-8") as f:
        f.write(script)

    print(f"[Main] 已输出脚本: {OUTPUT_SCRIPT}")
    print("[Main] 可直接运行：python auto_basilisk_sim.py （需 Basilisk 环境正确配置）")


if __name__ == "__main__":
    import sys
    main(sys.argv[1])
