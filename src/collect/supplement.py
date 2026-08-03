"""行业媒体 RSS 采集 + 关键词过滤。

采集机器人/具身智能相关的行业媒体、论坛、新闻站 RSS，
按 keywords.yaml 过滤，只保留通俗报道（非论文）。
"""

from __future__ import annotations

from pathlib import Path

import feedparser

from .base import Article, make_session, parse_config_yaml

DEFAULT_KEYWORDS = Path(__file__).resolve().parents[2] / "config" / "keywords.yaml"
DEFAULT_SOURCES = Path(__file__).resolve().parents[2] / "config" / "sources.yaml"

# 行业 RSS 源（公开、稳定、已实测可用）
INDUSTRY_RSS = [
    {"name": "IEEE Spectrum Robotics", "url": "https://spectrum.ieee.org/feeds/topic/robotics.xml"},
    {"name": "InfoQ 机器人", "url": "https://www.infoq.cn/feed/topic/106"},
    {"name": "36氪", "url": "https://36kr.com/feed"},
    {"name": "量子位", "url": "https://www.qbitai.com/feed"},
    {"name": "极客公园", "url": "https://www.geekpark.net/rss"},
    {"name": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/feed/"},
    {"name": "VentureBeat AI", "url": "https://venturebeat.com/category/ai/feed/"},
    {"name": "The Verge AI", "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"},
]


class KeywordFilter:
    """按关键词过滤文章。"""

    def __init__(self, config_path: str | Path = DEFAULT_KEYWORDS):
        cfg = parse_config_yaml(str(config_path)) or {}
        self.keywords = [str(k).lower() for k in cfg.get("keywords", [])]
        self.exclude = [str(k).lower() for k in cfg.get("exclude", [])]
        self.match_all = [str(k).lower() for k in cfg.get("match_all", [])]

    def is_related(self, title: str, summary: str = "") -> bool:
        """判断文章是否与具身智能/机器人主题相关。"""
        text = f"{title} {summary}".lower()
        if any(ex in text for ex in self.exclude):
            return False
        if self.match_all:
            return all(kw in text for kw in self.match_all)
        return any(kw in text for kw in self.keywords)


class IndustryRSSCollector:
    """行业媒体 RSS 采集器。"""

    def __init__(self, timeout: int = 30, keyword_config: str | Path = DEFAULT_KEYWORDS):
        self.timeout = timeout
        self.filter = KeywordFilter(keyword_config)

    def collect_all(self, feeds: list[dict] | None = None) -> list[Article]:
        """采集所有 RSS 源并按关键词过滤。"""
        feeds = feeds or INDUSTRY_RSS
        session = make_session(timeout=self.timeout)
        articles: list[Article] = []
        for feed_cfg in feeds:
            try:
                resp = session.get(feed_cfg["url"], headers={"Accept": "application/rss+xml"})
                resp.raise_for_status()
                feed = feedparser.parse(resp.content)
                for entry in feed.entries:
                    title = entry.get("title", "").strip()
                    summary = entry.get("summary", "").strip()
                    if not self.filter.is_related(title, summary):
                        continue
                    articles.append(
                        Article(
                            title=title,
                            url=entry.get("link", "").strip(),
                            account=feed_cfg["name"],
                            published_at=entry.get("published", "") or entry.get("updated", ""),
                            content=summary,
                            source="rss",
                        )
                    )
            except Exception:
                continue
        return articles
