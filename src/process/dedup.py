"""去重模块：基于指纹 + 标题相似度。"""

from __future__ import annotations

import difflib
import re
from collections import defaultdict

from ..collect.base import Article

_NORM = re.compile(r"[^\w\u4e00-\u9fa5]")


def _norm_title(title: str) -> str:
    return _NORM.sub("", (title or "").lower())


class Deduper:
    """按指纹和规范化标题去重。"""

    def __init__(self, title_threshold: float = 0.9):
        self.title_threshold = title_threshold
        self._seen_fp: set[str] = set()
        self._seen_titles: list[str] = []
        self._title_groups: dict[str, list[str]] = defaultdict(list)

    def dedup(self, articles: list[Article]) -> list[Article]:
        """返回去重后的文章列表（保序）。"""
        result: list[Article] = []
        for art in articles:
            fp = art.fingerprint
            if fp in self._seen_fp:
                continue
            nt = _norm_title(art.title)
            if not nt:
                continue
            if self._is_dup_title(nt):
                continue
            self._seen_fp.add(fp)
            self._seen_titles.append(nt)
            self._title_groups[nt[:8]].append(nt)
            result.append(art)
        return result

    def _is_dup_title(self, nt: str) -> bool:
        for other in self._seen_titles:
            ratio = difflib.SequenceMatcher(None, nt, other).ratio()
            if ratio >= self.title_threshold:
                return True
        # 按前缀分组内快速比较，减少 O(n^2)
        for other in self._title_groups.get(nt[:8], []):
            if other == nt:
                return True
        return False
