"""采集编排：整合主源、备源、补充源，实现主备降级。

调度逻辑:
1. 主源 RSSHub 采集公众号；某公众号失败则记入 failed
2. 若 RSSHub 整体失败或返回为空，降级到搜狗微信按关键词采集
3. 补充 arXiv + 行业 RSS
4. 返回 (articles, report) 其中 report 记录各源状态供告警/日志
"""

from __future__ import annotations

from pathlib import Path

from .base import Article, parse_config_yaml
from .rsshub import RSSHubCollector
from .sogou import SogouCollector
from .supplement import ArxivCollector, IndustryRSSCollector

DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "config" / "accounts.yaml"


class CollectorOrchestrator:
    """采集编排器，返回文章列表与采集报告。"""

    def __init__(self, config_path: str | Path = DEFAULT_CONFIG):
        self.config = parse_config_yaml(str(config_path)) or {"accounts": []}
        self.report: dict = {"rsshub": [], "sogou": [], "supplement": []}

    def collect(self, with_supplement: bool = True) -> list[Article]:
        accounts = [a["name"] for a in self.config.get("accounts", []) if a.get("enabled", True)]
        keywords: list[str] = []
        for a in self.config.get("accounts", []):
            if not a.get("enabled", True):
                continue
            keywords.extend(a.get("keywords") or [a.get("name", "")])

        articles: list[Article] = []
        rsshub_failed = False

        # 主源: RSSHub
        try:
            rsshub = RSSHubCollector()
            rss_articles = rsshub.collect_many(accounts)
            articles.extend(rss_articles)
            self.report["rsshub"] = [a.url for a in rss_articles]
            if not rss_articles:
                rsshub_failed = True
        except Exception as e:
            rsshub_failed = True
            self.report["rsshub_error"] = str(e)

        # 备源: 搜狗（主源失败或空时降级）
        if rsshub_failed or not self.report["rsshub"]:
            try:
                sogou = SogouCollector()
                sogou_articles = sogou.collect_keywords(keywords)
                articles.extend(sogou_articles)
                self.report["sogou"] = [a.url for a in sogou_articles]
            except Exception as e:
                self.report["sogou_error"] = str(e)

        # 补充源
        if with_supplement:
            try:
                arxiv = ArxivCollector()
                articles.extend(arxiv.collect())
            except Exception as e:
                self.report["arxiv_error"] = str(e)
            try:
                rss = IndustryRSSCollector()
                articles.extend(rss.collect_all())
            except Exception as e:
                self.report["rss_error"] = str(e)
            self.report["supplement"] = [
                a.url for a in articles if a.source in ("arxiv", "rss")
            ]

        return articles
