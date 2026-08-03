"""采集编排：整合行业媒体 RSS 采集。

调度逻辑:
1. 读取 config/sources.yaml 启用源
2. 逐源采集，单源失败不阻塞
3. 返回 (articles, report) 其中 report 记录各源状态供日志/告警
"""

from __future__ import annotations

from pathlib import Path

from .base import Article, parse_config_yaml
from .supplement import INDUSTRY_RSS, IndustryRSSCollector

DEFAULT_SOURCES = Path(__file__).resolve().parents[2] / "config" / "sources.yaml"


class CollectorOrchestrator:
    """采集编排器，返回文章列表与采集报告。"""

    def __init__(self, sources_path: str | Path = DEFAULT_SOURCES):
        cfg = parse_config_yaml(str(sources_path)) or {}
        self.sources = [s for s in cfg.get("sources", []) if s.get("enabled", True)]
        self.report: dict = {"sources": [], "errors": []}

    def collect(self) -> list[Article]:
        feeds = [{"name": s["name"], "url": s["url"]} for s in self.sources] or INDUSTRY_RSS
        collector = IndustryRSSCollector()
        articles = collector.collect_all(feeds)

        # 记录各源采集结果
        by_name: dict[str, list[str]] = {}
        for a in articles:
            by_name.setdefault(a.account, []).append(a.url)
        self.report["sources"] = [
            {"name": name, "count": len(urls)} for name, urls in by_name.items()
        ]
        return articles
