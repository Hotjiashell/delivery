# 交付使用说明

包括多query生成检索和知识抽取的代码，在 `delivery` 目录下运行以下命令。

## 多 Query 生成与检索

```bash
(cd query_rewrite && python evaluate.py all --method custom-multi --prompt-file prompts/konwledge_multi_query.txt \
  --query-output results/multi_queries.json --output results/multi_retrieval.json)
```

模型、数据输入输出路径配置见 [Query 改写与检索](query_rewrite/README.md)。

## 知识抽取

```bash
python -m extract_knowledge
```

模型、数据输入输出路径配置见 [知识抽取](extract_knowledge/README.md)。

### 测试流程

1. 评估抽取知识前的多 Query 检索效果。

   ```bash
   (cd query_rewrite && python evaluate.py all --method custom-multi --prompt-file prompts/konwledge_multi_query.txt \
     --query-output results/no_4_11_knowledge/queries.json --output results/no_4_11_knowledge/results.json)
   ```

2. 收集badcase。

   ```bash
   python query_rewrite/collect_badcases.py \
     query_rewrite/results/no_4_11_knowledge/results.json \
     query_rewrite/data/case_example.json --cutoff 10 --output results/no_4_11_knowledge/badcase.json
   ```

3. 根据badcase抽取知识。

   ```bash
   python -m extract_knowledge results/no_4_11_knowledge/badcase.json --output-dir outputs/run_001
   ```

4. 评估抽取知识后的效果。

   ```bash
   (cd query_rewrite && python evaluate.py all --method custom-multi \
     --prompt-file ../outputs/run_001/final/final_prompt.txt \
     --query-output results/with_4_11_knowledge/queries.json --output results/with_4_11_knowledge/results.json)
   ```

对照两个 `results.json` 中的 Recall@K，查看加入新知识前后的检索效果。
