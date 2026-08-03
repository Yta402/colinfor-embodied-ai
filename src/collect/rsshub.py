"""主源采集：RSSHub 公众号路由。

RSSHub 需自建服务。本项目设计为兼容任意 RSSHub 部署地址，
通过环境变量 RSSHUB_BASE 指定（默认 https://rsshub.app 公共实例）。
公众号文章通过 RSSHub 的公众号路由获取（微信读书 / 搜狗）。

注意：公共实例可能限流；生产环境建议自建 RSSHub。
"""

from __future__ import annotations

import os

import feedparser

from .base import Article, make_session, polite_sleep

DEFAULT_BASE = "https://rsshub.app"


class RSSHubCollector:
    """基于 RSSHub 的公众号/媒体源采集器。"""

    def __init__(self, base_url: str | None = None, timeout: int = 30):
        self.base = (base_url or os.getenv("RSSHUB_BASE", DEFAULT_BASE)).rstrip("/")
        self.timeout = timeout

    def _route_url(self, route: str, params: str = "") -> str:
        """构造 RSSHub 路由 URL。"""
        return f"{self.base}/{route}{params}"

    def fetch_feed(self, route: str, params: str = "", account: str = "") -> list[Article]:
        """抓取单个 RSS 源并转换为 Article 列表。

        route   - RSSHub 路由，如 'wechat/公众号名'
        params  - 追加查询参数
        account - 展示用账号名（缺省取 route）
        """
        url = self._route_url(route, params)
        session = make_session(timeout=self.timeout)
        resp = session.get(url, headers={"Accept": "application/xml"})
        resp.raise_for_status()

        feed = feedparser.parse(resp.content)
        articles: list[Article] = []
        for entry in feed.entries:
            articles.append(
                Article(
                    title=entry.get("title", "").strip(),
                    url=entry.get("link", "").strip(),
                    account=account or route,
                    published_at=entry.get("published", "") or entry.get("updated", ""),
                    content=entry.get("summary", "").strip(),
                    source="rsshub",
                )
            )
        return articles

    def collect_account(self, name: str) -> list[Article]:
        """采集单个公众号。

        依次尝试微信读书路由（wechat）与搜狗路由（wechat/sogou），
        返回非空结果，任一失败则降级下一个。
        """
        attempts = [
            f"wechat/{name}",
            f"wechat/sogou/{name}",
        ]
        for route in attempts:
            try:
                articles = self.fetch_feed(route=route, account=name)
                if articles:
                    return articles
            except Exception:
                polite_sleep(2, 4)
                continue
        return []

    def collect_many(self, accounts: list[str]) -> list[Article]:
        """批量采集多个公众号，逐个容错。"""
        all_articles: list[Article] = []
        for name in accounts:
            try:
                all_articles.extend(self.collect_account(name))
            except Exception:
                continue
            polite_sleep(1, 2)
        return all_articles
