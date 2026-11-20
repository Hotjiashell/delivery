"""Query-generation contracts and prompt-based query rewriting methods.

To add a query rewriting approach, implement ``QueryGenerator.generate`` and
pass the instance to ``Evaluator``.  The evaluation and retrieval code does
not need to change.
"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

CUSTOM_METHOD = "custom"
CUSTOM_MULTI_METHOD = "custom_multi"
SUPPORTED_QUERY_METHODS = (CUSTOM_METHOD, CUSTOM_MULTI_METHOD)
MAX_MULTI_QUERIES = 3
DIALOGUE_PLACEHOLDER = "{dialogue}"


class QueryGenerationError(RuntimeError):
    """Raised when a model response cannot produce a non-empty query."""


class ChatCompletionsClient(Protocol):
    """The small subset of an OpenAI-compatible client used by the generators."""

    @property
    def chat(self) -> Any:
        """Expose the OpenAI chat namespace."""


class QueryGenerator(ABC):
    """Stable extension point for all query rewriting strategies."""

    @abstractmethod
    def generate(self, dialogue: str) -> str:
        """Return one retrieval query for a complete dialogue."""


class MultiQueryGenerator(QueryGenerator):
    """Extension point for strategies that can propose several queries."""

    @abstractmethod
    def generate_queries(self, dialogue: str) -> list[str]:
        """Return one or more retrieval queries for a complete dialogue."""

    def generate(self, dialogue: str) -> str:
        return self.generate_queries(dialogue)[0]


@dataclass(frozen=True)
class LLMConfig:
    """Connection parameters for an OpenAI-compatible chat-completions API."""

    base_url: str
    model_name: str
    api_key: str
    temperature: float = 0.0

    def validate(self) -> None:
        missing = [
            name
            for name, value in (
                ("base_url", self.base_url),
                ("model_name", self.model_name),
                ("api_key", self.api_key),
            )
            if not value or not value.strip()
        ]
        if missing:
            raise ValueError(f"missing LLM configuration: {', '.join(missing)}")


def build_openai_client(config: LLMConfig) -> ChatCompletionsClient:
    """Create the optional SDK client only when a real model call is needed."""

    config.validate()
    try:
        from openai import OpenAI
    except ImportError as exc:  # pragma: no cover - environment-specific path
        raise RuntimeError(
            "The 'openai' package is required for model calls. "
            "Install dependencies with: pip install -r requirements.txt"
        ) from exc
    return OpenAI(api_key=config.api_key, base_url=config.base_url)


def normalize_query_method(method: str) -> str:
    """Normalize hyphenated and underscored method names."""

    if not isinstance(method, str) or not method.strip():
        raise ValueError("query method must be a non-empty string")
    normalized = method.strip().lower().replace("-", "_")
    if normalized not in SUPPORTED_QUERY_METHODS:
        supported = ", ".join(SUPPORTED_QUERY_METHODS)
        raise ValueError(f"unsupported query method '{method}'; supported methods: {supported}")
    return normalized


def extract_query(model_content: str) -> str:
    """Extract ``query`` from a single-query JSON response.

    Some model providers include a Markdown fence while others return the JSON
    object directly, so both forms are accepted.  We intentionally reject a
    malformed answer instead of silently sending arbitrary text to retrieval.
    """

    if not isinstance(model_content, str) or not model_content.strip():
        raise QueryGenerationError("model returned empty content")

    candidates = re.findall(
        r"```(?:json)?\s*(\{.*?\})\s*```",
        model_content,
        flags=re.IGNORECASE | re.DOTALL,
    )
    candidates.append(model_content.strip())

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict) and isinstance(parsed.get("query"), str):
            query = parsed["query"].strip()
            if query:
                return query

    raise QueryGenerationError("model response must contain a non-empty JSON 'query'")


def extract_queries(model_content: str, *, max_queries: int = MAX_MULTI_QUERIES) -> list[str]:
    """Extract one or more queries from a multi-query JSON response.

    ``query`` may be a JSON array (the intended shape) or a single string, so
    both forms are accepted. Duplicate and empty entries are dropped while
    preserving order, and the result is capped at ``max_queries``.
    """

    if not isinstance(model_content, str) or not model_content.strip():
        raise QueryGenerationError("model returned empty content")

    candidates = re.findall(
        r"```(?:json)?\s*(\{.*?\})\s*```",
        model_content,
        flags=re.IGNORECASE | re.DOTALL,
    )
    candidates.append(model_content.strip())

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if not isinstance(parsed, dict):
            continue
        raw_query = parsed.get("query")
        if isinstance(raw_query, str):
            raw_values: list[Any] = [raw_query]
        elif isinstance(raw_query, list):
            raw_values = raw_query
        else:
            continue

        queries: list[str] = []
        for value in raw_values:
            if not isinstance(value, str):
                continue
            stripped = value.strip()
            if stripped and stripped not in queries:
                queries.append(stripped)
        if queries:
            return queries[:max_queries]

    raise QueryGenerationError("model response must contain a non-empty JSON 'query'")


def _call_model(
    client: ChatCompletionsClient,
    model_name: str,
    prompt: str,
    temperature: float,
) -> str:
    """Call the chat-completions endpoint with thinking disabled and return its text."""

    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        extra_body={
            "chat_template_kwargs": {"enable_thinking": False},
        },
    )
    try:
        return response.choices[0].message.content
    except (AttributeError, IndexError, TypeError) as exc:
        raise QueryGenerationError("model response has no first message content") from exc


def load_prompt_template(path: str) -> str:
    """Read a custom prompt template from disk and validate its placeholder.

    The file must contain the literal ``{dialogue}`` placeholder.
    """

    source = Path(path)
    try:
        content = source.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ValueError(f"prompt file does not exist: {source}") from exc
    except OSError as exc:
        raise ValueError(f"could not read prompt file: {source}: {exc}") from exc

    if not content.strip():
        raise ValueError(f"prompt file is empty: {source}")
    if DIALOGUE_PLACEHOLDER not in content:
        raise ValueError(
            f"prompt file must contain a '{DIALOGUE_PLACEHOLDER}' placeholder: {source}"
        )
    return content


class _PromptGeneratorBase:
    """Shared validation and prompt binding for prompt-based generators."""

    def __init__(
        self,
        client: ChatCompletionsClient,
        model_name: str,
        method: str,
        temperature: float = 0.0,
        prompt_template: str | None = None,
    ) -> None:
        if not model_name or not model_name.strip():
            raise ValueError("model_name must not be empty")
        self._client = client
        self._model_name = model_name
        self._method = normalize_query_method(method)
        if not isinstance(temperature, (int, float)) or isinstance(temperature, bool) or not 0 <= temperature <= 2:
            raise ValueError("temperature must be between 0 and 2")
        self._temperature = float(temperature)
        if not prompt_template or not prompt_template.strip():
            raise ValueError(f"prompt_template is required for the '{self._method}' method")
        self._prompt_template = prompt_template

    @property
    def method(self) -> str:
        """Canonical method name used to create this generator."""

        return self._method

    def _render_prompt(self, dialogue: str) -> str:
        if not dialogue or not dialogue.strip():
            raise ValueError("dialogue must not be empty")
        # The prompt includes a literal JSON example, whose braces must not be
        # interpreted as ``str.format`` fields.
        return self._prompt_template.replace("{dialogue}", dialogue)


class PromptQueryGenerator(_PromptGeneratorBase, QueryGenerator):
    """One-shot generator backed by one named prompt template."""

    def generate(self, dialogue: str) -> str:
        prompt = self._render_prompt(dialogue)
        content = _call_model(self._client, self._model_name, prompt, self._temperature)
        return extract_query(content)


class PromptMultiQueryGenerator(_PromptGeneratorBase, MultiQueryGenerator):
    """Generator that proposes several queries, using a custom prompt template."""

    def generate_queries(self, dialogue: str) -> list[str]:
        prompt = self._render_prompt(dialogue)
        content = _call_model(self._client, self._model_name, prompt, self._temperature)
        return extract_queries(content)


def create_query_generator(
    config: LLMConfig,
    method: str,
    *,
    prompt_file: str | None = None,
) -> QueryGenerator:
    """Create a generator using a prompt template loaded from disk."""

    normalized = normalize_query_method(method)
    if not prompt_file or not prompt_file.strip():
        raise ValueError(f"prompt_file is required for the '{normalized}' method")
    prompt_template = load_prompt_template(prompt_file)
    generator_class = PromptMultiQueryGenerator if normalized == CUSTOM_MULTI_METHOD else PromptQueryGenerator
    return generator_class(
        build_openai_client(config),
        config.model_name,
        normalized,
        temperature=config.temperature,
        prompt_template=prompt_template,
    )
