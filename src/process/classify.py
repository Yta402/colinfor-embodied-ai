"""LLM 归类 + 摘要：调用 DeepSeek 对文章打多标签并生成摘要。

一次调用同时完成摘要与标签归类，降低 API 成本。
"""

from __future__ import annotations

import json
import os

from ..collect.base import Article
from .common import get_client, llm_chat, load_tags, parse_json_safe

DEFAULT_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")

SYSTEM_PROMPT = """你是一个具身智能行业资讯分析师。给定一篇文章的标题与正文，输出 JSON：
{
  "summary": "3-5句话的中文摘要，突出关键信息（技术要点/公司/金额/时间等）",
  "tags": ["标签id", ...]
}
标签必须严格从给定列表中挑选，可同时贴多个标签；若无法确定，tags 可为空数组。
只输出 JSON，不要输出其他内容。"""


class LLMClassifier:
    """DeepSeek 摘要 + 多标签归类器。"""

    def __init__(self, tags_config_path: str | None = None, model: str | None = None):
        self.model = model or DEFAULT_MODEL
        self.tags = load_tags(tags_config_path) if tags_config_path else load_tags()
        self.tag_by_id = {t["id"]: t for t in self.tags}
        self.tag_desc = "\n".join(
            f"- {t['id']}({t['name']}): {t['desc']}" for t in self.tags
        )

    def _tag_prompt(self) -> str:
        return f"可用标签:\n{self.tag_desc}"

    def classify(self, article: Article) -> Article:
        """对单篇文章打标+摘要，异常时保留原文不中断。"""
        try:
            client = get_client()
            user_content = (
                f"{self._tag_prompt()}\n\n标题: {article.title}\n"
                f"正文: {article.content[:3000]}"
            )
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ]
            raw = llm_chat(client, messages, model=self.model)
            data = parse_json_safe(raw)
            summary = str(data.get("summary", "")).strip()
            tag_ids = data.get("tags") or []
            if isinstance(tag_ids, list):
                valid = [str(t) for t in tag_ids if str(t) in self.tag_by_id]
            else:
                valid = []
            if summary:
                article.summary = summary
            article.tags = valid
        except Exception as e:
            article.tags = []
            article.summary = ""
            article._classify_error = str(e)  # type: ignore[attr-defined]
        return article

    def classify_many(self, articles: list[Article]) -> list[Article]:
        """批量归类，单篇失败不阻塞。"""
        for art in articles:
            self.classify(art)
        return articles
