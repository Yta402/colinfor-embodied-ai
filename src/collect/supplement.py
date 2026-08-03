"""补充源采集：arXiv + 行业站点 RSS。

保证信息覆盖度，避免仅依赖公众号。
- arXiv: 具身智能相关分类（cs.RO 机器人学等）
- 行业 RSS: 常见机器人/AI 科技媒体
"""

from __future__ import annotations

from urllib.parse import urlencode

import feedparser

from .base import Article, make_session

ARXIV_API = "https://export.arxiv.org/api/query"

# 行业 RSS 源（公开、稳定）
INDUSTRY_RSS = [
    {"name": "IEEE Spectrum Robotics", "url": "https://spectrum.ieee.org/rss/robotics.xml"},
    {"name": "The Robot Report", "url": "https://www.therobotreport.com/feed/"},
    {"name": "MIT Tech Review AI", "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed"},
]


class ArxivCollector:
    """arXiv 具身智能论文采集。"""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    def collect(self, query: str = "embodied intelligence OR humanoid robot", max_results: int = 20) -> list[Article]:
        params = {
            "search_query": query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
        session = make_session(timeout=self.timeout)
        resp = session.get(ARXIV_API, params=urlencode(params))
        resp.raise_for_status()

        feed = feedparser.parse(resp.content)
        articles: list[Article] = []
        for entry in feed.entries:
            articles.append(
                Article(
                    title=entry.get("title", "").replace("\n", " ").strip(),
                    url=entry.get("link", "").strip(),
                    account="arXiv",
                    published_at=entry.get("published", ""),
                    content=entry.get("summary", "").replace("\n", " ").strip(),
                    source="arxiv",
                )
            )
        return articles


class IndustryRSSCollector:
    """行业站点 RSS 采集。"""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    def collect_all(self, feeds: list[dict] | None = None) -> list[Article]:
        feeds = feeds or INDUSTRY_RSS
        session = make_session(timeout=self.timeout)
        articles: list[Article] = []
        for feed_cfg in feeds:
            try:
                resp = session.get(feed_cfg["url"], headers={"Accept": "application/rss+xml"})
                resp.raise_for_status()
                feed = feedparser.parse(resp.content)
                for entry in feed.entries:
                    articles.append(
                        Article(
                            title=entry.get("title", "").strip(),
                            url=entry.get("link", "").strip(),
                            account=feed_cfg["name"],
                            published_at=entry.get("published", "") or entry.get("updated", ""),
                            content=entry.get("summary", "").strip(),
                            source="rss",
                        )
                    )
            except Exception:
                continue
        return articles
