"""备源采集：搜狗微信搜索。

当 RSSHub 失效时降级使用。搜狗微信反爬较强：
- 使用随机 UA + 随机延时
- 解析结果列表，命中验证码时抛出异常交由上层告警暂停
"""

from __future__ import annotations

import re
from urllib.parse import quote, urljoin

import requests

from .base import Article, make_session, polite_sleep

SEARCH_URL = "https://weixin.sogou.com/weixin"

# 验证码 / 反爬特征
_ANTIBOT_MARKERS = [
    "antispider",
    "请输入验证码",
    "验证码",
    "访问过于频繁",
]

_TITLE_RE = re.compile(r"<h3>.*?<a[^>]*href=\"(?P<url>[^\"]+)\"[^>]*>(?P<title>.*?)</a>", re.S)
_ACCOUNT_RE = re.compile(r'<a[^>]*class="account"[^>]*>(?P<name>.*?)</a>', re.S)
_TIME_RE = re.compile(r'<span[^>]*class="s2"[^>]*>\s*(?P<time>.*?)\s*</span>', re.S)
_STRIP_TAG = re.compile(r"<[^>]+>")


class SogouCollector:
    """搜狗微信搜索采集器。"""

    def __init__(self, timeout: int = 15):
        self.timeout = timeout

    def _search(self, keyword: str, page: int = 1) -> str:
        session = make_session(timeout=self.timeout)
        params = {
            "type": 2,  # 2=文章, 1=公众号
            "query": keyword,
            "page": page,
        }
        resp = session.get(SEARCH_URL, params=params)
        resp.encoding = "utf-8"
        html = resp.text
        if any(marker in html for marker in _ANTIBOT_MARKERS):
            raise RuntimeError("搜狗微信触发反爬/验证码，请人工介入或稍后重试")
        return html

    @staticmethod
    def _clean(s: str) -> str:
        return _STRIP_TAG.sub("", s).strip()

    def _parse_results(self, html: str, keyword: str) -> list[Article]:
        articles: list[Article] = []
        for m in _TITLE_RE.finditer(html):
            url = m.group("url")
            # 搜狗返回相对跳转链接，需要拼接域名
            if url.startswith("/"):
                url = urljoin(SEARCH_URL, url)
            title = self._clean(m.group("title"))
            if not title:
                continue
            articles.append(
                Article(
                    title=title,
                    url=url,
                    account=keyword,
                    published_at="",
                    content="",
                    source="sogou",
                )
            )
        return articles

    def collect_keyword(self, keyword: str, max_pages: int = 1) -> list[Article]:
        """按关键词搜索采集，支持多页。"""
        all_articles: list[Article] = []
        for page in range(1, max_pages + 1):
            try:
                html = self._search(keyword, page=page)
            except requests.RequestException:
                break
            results = self._parse_results(html, keyword)
            if not results:
                break
            all_articles.extend(results)
            polite_sleep(3, 6)  # 搜狗反爬强，延时放大
        return all_articles

    def collect_keywords(self, keywords: list[str], max_pages: int = 1) -> list[Article]:
        """批量关键词采集。"""
        all_articles: list[Article] = []
        for kw in keywords:
            try:
                all_articles.extend(self.collect_keyword(kw, max_pages=max_pages))
            except RuntimeError:
                raise  # 反爬异常向上传播，触发告警
            except Exception:
                continue
            polite_sleep(3, 6)
        return all_articles
