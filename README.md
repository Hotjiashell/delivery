# 交付使用说明

在 `delivery` 目录下运行以下命令。

## 单 Query 生成与检索

```bash
(cd query_rewrite && python evaluate.py all --method custom --prompt-file prompts/custom.txt \
  --query-output results/single_queries.json --output results/single_retrieval.json)
```

## 多 Query 生成与检索

```bash
(cd query_rewrite && python evaluate.py all --method custom-multi --prompt-file prompts/konwledge_multi_query.txt \
  --query-output results/multi_queries.json --output results/multi_retrieval.json)
```

依赖、模型配置和分步运行命令见 [Query 改写与检索](query_rewrite/README.md)。

## 知识抽取

```bash
python -m extract_knowledge
```

输入、模型配置和提示词产物见 [知识抽取](extract_knowledge/README.md)。
