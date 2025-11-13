## 使用流程小结

1. **准备知识库文档**

   * 把 Basilisk 文档 / 示例代码拷到 `data/docs/` 下
   * 文件类型支持 `.txt .md .rst .py`

2. **安装依赖**

```bash
pip install -r requirements.txt
```

3. **构建 RAG 知识库**

```bash
python rule_extractor.py
python kb_build.py
```
将生成：
```bash
kb/rules.json
kb/bsk_index.faiss
kb/bsk_chunks.json
```

4. **写一个 Flowchart.js 文件**（可参考 `examples/simple.flow`）

5. **生成 Basilisk 仿真脚本**

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

