## 使用流程小结


1. **安装依赖**

```bash
pip install -r requirements.txt
```

2. **写一个 Flowchart.js 文件**（可参考 `examples/simple.flow`）

3. **生成 Basilisk 仿真脚本**

```bash
python main.py examples/simple.flow
```

6. **运行自动生成的脚本**

```bash
python basilisk_auto_sim.py
```

> 注意：
>
> * 生成的脚本里对 Basilisk 的调用是一个**“合理但未验证版本”**，API 名称可能需要你依据实际 Basilisk 版本略微改动。
> * RAG 的作用主要是**把相关文档片段作为注释附在每个步骤旁边**，辅助你扩展规则或改代码。整个过程完全无 LLM，逻辑全可控。

---

## 调试日志v1
1. 代码关键词匹配改为全词匹配。
2. 因为最后一步默认是仿真运行，读取数据和画图从`example_to_flow`中删去，视需要再添加。
3. 仿真时间和数据点数量，没有提取出来，需要自己设置。
4. 流程图顺序可能不对，未使用`module_dependency`
5. 未使用自动提取规则`rule_extract`和`kb_build`.
6. 消息机制运行报错