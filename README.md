## 使用流程小结
第一版还保有自动抽取规则的整体流程，但抽取模块出现路径错误等情况；所以目前第二版，使用手动模板规则。

1. **安装依赖**

```bash
pip install -r requirements.txt
```

2. **写一个 Flowchart.js 文件**（可参考 `examples/simple.flow`）
   使用英语，用词可参考`codegen.py`的`KEY_MAP`字典。

3. **生成 Basilisk 仿真脚本**

```bash
python main.py examples/simple.flow
```

4. **运行自动生成的脚本**

需要自己装Basilisk包，或者通过源码安装
```bash
python basilisk_auto_sim.py
```

> 注意：
>
> * 生成的脚本里对 Basilisk 的调用是一个**“合理但未验证版本”**，API 名称可能需要你依据实际 Basilisk 版本略微改动。
> * RAG 的作用主要是**把相关文档片段作为注释附在每个步骤旁边**，辅助你扩展规则或改代码。整个过程完全无 LLM，逻辑全可控。

---

