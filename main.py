from config import OUTPUT_SCRIPT
from flow_parser import parse_flowchart
from codegen import assemble_script

def main(flow_path):
    flow_text = open(flow_path).read()
    tasks = parse_flowchart(flow_text)
    script = assemble_script(tasks)
    open(OUTPUT_SCRIPT, "w").write(script)
    print("Generated:", OUTPUT_SCRIPT)

if __name__ == "__main__":
    import sys
    main(sys.argv[1])
