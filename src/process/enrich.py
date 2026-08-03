"""字段补齐：清洗缺失字段（作者/发布时间/正文）。"""

from __future__ import annotations

import re
from datetime import datetime

from ..collect.base import Article

# 常见公众号正文版权尾注等噪音片段，用于截断
_NOISE_PATTERNS = [
    re.compile(r"点击.*关注.*获取更多", re.I),
    re.compile(r"欢迎转发.*朋友圈", re.I),
    re.compile(r"长按.*二维码.*关注", re.I),
    re.compile(r"如需转载.*授权", re.I),
]


class Enricher:
    """补全缺失字段并清洗正文。"""

    def enrich(self, articles: list[Article], today: str | None = None) -> list[Article]:
        today = today or datetime.now().strftime("%Y-%m-%d")
        for art in articles:
            art.title = (art.title or "").strip() or "无标题"
            art.url = (art.url or "").strip()
            art.account = (art.account or "").strip() or "未知"
            if not art.published_at:
                art.published_at = today
            art.content = self._clean_body(art.content)
        return articles

    @staticmethod
    def _clean_body(content: str) -> str:
        """去除正文噪音片段。"""
        cleaned = content
        for pat in _NOISE_PATTERNS:
            m = pat.search(cleaned)
            if m:
                cleaned = cleaned[: m.start()]
        return cleaned.strip()[:2000]
