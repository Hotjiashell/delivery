# 知识抽取

在 `delivery` 下运行。使用 Python 3.11 或更高版本，安装公用依赖。

```bash
python -m pip install -r query_rewrite/requirements.txt
python -m extract_knowledge --help
python -m extract_knowledge
```

运行前准备badcase，并配置 LLM、Embedding 和检索服务。

```bash
python -m extract_knowledge results/badcases.json --output-dir outputs/run_001
```

## 收集badcase

在 `delivery` 下运行。第一个位置参数是检索结果，第二个位置参数是案例文件，--output指定badcase输出路径。

```bash
python query_rewrite/collect_badcases.py \
  query_rewrite/results/retrieval.json query_rewrite/data/case_example.json \
  --output results/badcases_single.json
```

## 配置

默认读取 [config.json](config.json)，可用 `--config` 指定其他文件。配置文件中的相对路径以 `delivery` 为基准，命令行中的相对路径以当前工作目录为基准。

| 配置 | 说明 |
| --- | --- |
| `extract_knowledge.badcases` | badcase路径数组。报告由 `collect_badcases.py` 生成，命令行位置参数可覆盖此项。 |
| `extract_knowledge.knowledge`、`prompts_file` | 已有知识文本和抽取阶段提示词，可用 `--knowledge`、`--prompts-file` 覆盖。 |
| `extract_knowledge.cases`、`dialogues` | 可选的案例映射和原始对话 JSON，可用 `--cases`、`--dialogues` 覆盖。案例按 GT ID 查找，对话按 `call_sno` 补齐。 |
| `extract_knowledge.output_dir`、`resume` | 输出目录和检查点复用。用 `--output-dir` 改路径，`--resume` 或 `--no-resume` 切换复用。 |
| `extract_knowledge.concurrency`、`timeout`、`retries`、`max_tokens` | LLM 并发、超时秒数、首次失败后的重试次数和输出 token 上限。对应 `--concurrency`、`--timeout`、`--retries`、`--max-tokens`。 |
| `extract_knowledge.keyword_batch_size`、`max_examples`、`min_cluster_size`、`precluster_similarity_threshold` | 关键词批大小、每簇样例上限、低频簇过滤阈值和预聚类相似度阈值。簇内去重坏例数小于等于 `min_cluster_size` 时过滤，设为 0 可关闭过滤。对应同名连字符选项。 |
| `llm` | `base_url`、`model_name`、`api_key_env` 和 `temperature`。默认可从 `OPENAI_BASE_URL`、`OPENAI_MODEL`、`OPENAI_API_KEY` 读取连接参数。 |
| `embedding` | 预聚类的接口、模型、密钥和批处理设置。可用 `EMBEDDING_BASE_URL`、`EMBEDDING_MODEL`、`EMBEDDING_API_KEY`。未配置 Embedding 密钥时使用 LLM 密钥。 |
| `feedback`、`review_llm` | 交付配置默认开启反馈验证。配置 `retrieval_url`、`top_k`、`fusion_method`、`min_recall`、`max_rounds` 等。用 `max_entries` 限制验证的新知识条数，0 表示全部。用 `review_llm` 覆盖评审模型配置。 |
| `research` | 默认开启。可通过 `research.enabled` 关闭。可配置检索地址、`top_k`、`max_searches`、`min_dialogues`、并发和超时。 |

## 输出与提示词

输出目录下的 `final/knowledge.json` 和 `final/knowledge.txt` 保存新知识，`final/final_prompt.txt` 结合本轮已有知识和全部产出的新知识。已有知识快照、运行摘要和各阶段检查点位于输出目录。生成的提示词可传给 Query 改写的 `--method custom-multi --prompt-file`。

单独重建提示词时，传入输出目录、含 `{knowledge}` 的模板和新知识条数。条数为 0 时只填入已有知识。

```bash
python -m extract_knowledge.build_eval_prompt outputs/run_001 \
  extract_knowledge/eval_prompt_template.txt 10
```
