# Query 改写与检索

使用 Python 3.11 或更高版本。在 `delivery/query_rewrite` 下运行命令。

```bash
python -m pip install -r requirements.txt
python evaluate.py --help
```

## 配置

默认读取 [config.json](config.json)。用 `--config` 指定其他配置。命令行参数优先于 JSON 中的对应配置，相对路径根据当前工作目录解析。

| 配置 | 说明 |
| --- | --- |
| `llm.base_url`、`llm.model_name` | OpenAI 兼容接口地址和模型名，可通过 `--base-url`、`--model` 覆盖。配置缺省时读取 `OPENAI_BASE_URL`、`OPENAI_MODEL`。 |
| `llm.api_key_env` | 密钥所在的环境变量，交付配置使用 `OPENAI_API_KEY`。也支持 `llm.api_key` 和 `--api-key`。 |
| `llm.temperature` | 采样温度，范围 0 到 2，默认 0。可用 `--temperature` 覆盖。 |
| `query_generation.method`、`prompt_file` | 生成模式与模板路径，可用 `--method`、`--prompt-file` 覆盖。 |
| `query_generation.input_path`、`output_path`、`concurrency` | 对话输入、Query JSON 输出、生成并发。在 `generate` 中用 `--input`、`--output`、`--concurrency` 覆盖。输入格式见 [示例对话](data/dialog_example.json)。 |
| `retrieval.input_path`、`output_path`、`concurrency` | Query JSON 输入、检索结果 JSON 输出、检索并发。在 `retrieve` 中用 `--input`、`--output`、`--concurrency` 覆盖。 |
| `retrieval.url`、`timeout` | 检索服务地址和超时秒数，可用 `--retrieval-url`、`--timeout` 覆盖。 |
| `retrieval.fusion_method`、`top_k` | 多路结果融合方式和保留条数。融合支持 `round_robin`（默认）和 `score`，默认保留 10 条。可用 `--fusion-method`、`--top-k` 覆盖。 |

模板须包含 `{dialogue}`。单 Query 模式 `custom` 要求模型输出 `{"query":"查询文本"}`。多 Query 模式 `custom-multi`（也接受 `custom_multi`）使用 `{"query":["查询一","查询二"]}`，最多保留三条去重后的 Query。

## 运行

```bash
python evaluate.py generate --method custom --prompt-file prompts/custom.txt
python evaluate.py retrieve
```

默认的 `retrieve` 读取 `results/generated_queries.json`。使用自定义生成路径时，用 `retrieve --input` 指向同一个文件。

`all` 会直接检索本次生成的 Query。用 `--query-input`、`--query-output`、`--query-concurrency` 配置生成阶段，用 `--retrieval-output` 和 `--retrieval-concurrency` 配置检索阶段。单双模式的完整命令见 [总 README](../README.md)。

`retrieve --retry-errors <已有检索结果>` 只重试检索失败的记录并合并结果。给 `retrieve` 或 `all` 加上 `--internal-time <秒数>` 可定时重试检索错误。对已有检索结果计算有标注指标时，使用 `python evaluate.py metrics --input <检索结果> --dataset <标注数据>`。
