"""采集层公共工具与数据结构。"""

from __future__ import annotations

import hashlib
import random
import time
from dataclasses import dataclass, field
from typing import Any

import requests


@dataclass
class Article:
    """一条采集到的文章记录。"""

    title: str
    url: str
    account: str
    published_at: str = ""
    content: str = ""
    source: str = ""
    tags: list[str] = field(default_factory=list)
    summary: str = ""

    @property
    def fingerprint(self) -> str:
        """基于标题+链接生成去重指纹。"""
        raw = f"{self.title.strip().lower()}|{self.url.strip()}".encode("utf-8")
        return hashlib.md5(raw).hexdigest()


def make_session(timeout: int = 15) -> requests.Session:
    """构造带随机 UA 的会话，用于降低反爬识别概率。"""
    uas = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/17.4 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/123.0 Safari/537.36",
    ]
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": random.choice(uas),
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
    )
    session.timeout = timeout
    return session


def polite_sleep(min_s: float = 1.0, max_s: float = 3.0) -> None:
    """随机延时，避免高频请求触发风控。"""
    time.sleep(random.uniform(min_s, max_s))


def clean_text(text: str, max_len: int = 2000) -> str:
    """清理空白字符并截断正文。"""
    lines = [ln.strip() for ln in (text or "").splitlines()]
    cleaned = "\n".join(ln for ln in lines if ln)
    return cleaned[:max_len]


def parse_config_yaml(path: str) -> Any:
    """读取 yaml 配置文件，失败时返回 None。"""
    try:
        import yaml

        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception:
        return None
