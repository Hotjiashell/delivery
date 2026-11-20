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
| `llm.temperature` | 采样温度，默认 0。可用 `--temperature` 覆盖。 |
| `query_generation.method`、`prompt_file` | 生成模式与query生成提示词路径，生成模式包括"custom"（自定义单query提示词）和"custom-multi"（自定义多query提示词）|
| `query_generation.input_path`、`output_path`、`concurrency` | 对话输入路径、Query输出路径、Query生成并发数。|
| `retrieval.input_path`、`output_path`、`concurrency` | Query输入路径、检索结果输出路径、检索并发数。 |
| `retrieval.url`、`timeout` | 检索服务地址和超时秒数，可用 `--retrieval-url`、`--timeout` 覆盖。 |
| `retrieval.fusion_method`、`top_k` | 多路结果融合方式和保留条数。融合支持 `round_robin`（默认）和 `score`，默认保留 10 条。可用 `--fusion-method`、`--top-k` 覆盖。 |

提示词模板须包含 `{dialogue}`。单 Query 模式 `custom` 要求模型输出 `{"query":"查询文本"}`。多 Query 模式 `custom-multi` 要求模型输出 `{"query":["查询一","查询二"]}`。

## 运行
可分步骤运行generate（生成query）和retrieve（利用生成的query进行检索），也可直接一次性运行all。
```bash
# 分步骤运行
python evaluate.py generate --method custom-multi --prompt-file prompts/konwledge_multi_query.txt
python evaluate.py retrieve
# 一次性运行
python evaluate.py all --method custom-multi --prompt-file prompts/konwledge_multi_query.txt
```