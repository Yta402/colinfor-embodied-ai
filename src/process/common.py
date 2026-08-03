"""处理层公共工具。"""

from __future__ import annotations

import json
import os
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None

DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "config" / "tags.yaml"


def load_tags(path: str | Path = DEFAULT_CONFIG) -> list[dict]:
    """读取标签配置，返回 [{id, name, desc, examples}, ...]"""
    from .base import parse_config_yaml  # noqa: F401

    import yaml

    with open(path, "r", encoding="utf-8") as f:
        return (yaml.safe_load(f) or {}).get("tags", [])


def get_client() -> "OpenAI":
    """构造 DeepSeek 客户端。依赖环境变量 DEEPSEEK_API_KEY。"""
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    if not api_key:
        raise RuntimeError("缺少 DEEPSEEK_API_KEY 环境变量")
    return OpenAI(api_key=api_key, base_url="https://api.deepseek.com")


def llm_chat(client: "OpenAI", messages: list[dict], model: str = "deepseek-chat", **kwargs) -> str:
    """调用 DeepSeek 对话接口，返回文本内容。"""
    if OpenAI is None:
        raise RuntimeError("缺少 openai 库，请安装 requirements")
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        response_format={"type": "json_object"},
        **kwargs,
    )
    return resp.choices[0].message.content or ""


def parse_json_safe(text: str, fallback: dict | None = None) -> dict:
    """宽松解析 LLM 返回的 JSON，容忍多余反引号/前后缀。"""
    fallback = fallback or {}
    try:
        return json.loads(text)
    except Exception:
        pass
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except Exception:
            pass
    return fallback
