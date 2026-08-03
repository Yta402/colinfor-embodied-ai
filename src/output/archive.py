"""归档合并：把当日文章合并进历史总表。"""

from __future__ import annotations

import csv
from pathlib import Path

from ..collect.base import Article
from .table import HEADERS, write_csv, write_xlsx


def load_history(history_csv: str | Path) -> list[Article]:
    """读取历史 CSV，还原为 Article 列表。"""
    path = Path(history_csv)
    articles: list[Article] = []
    if not path.exists():
        return articles
    with open(path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            articles.append(
                Article(
                    title=row.get("标题", ""),
                    url=row.get("链接", ""),
                    account=row.get("账号", ""),
                    published_at=row.get("日期", ""),
                    summary=row.get("摘要", ""),
                    tags=[t for t in (row.get("标签", "") or "").split("、") if t],
                    content=row.get("正文", ""),
                    source=row.get("来源", ""),
                )
            )
    return articles


def merge_into_history(
    daily_articles: list[Article],
    history_csv: str | Path,
    output_dir: str | Path,
    date: str,
    deduper=None,
) -> tuple[Path, Path]:
    """合并当日文章进历史，生成日报 + 更新总表。

    deduper - 复用去重器，按指纹过滤历史已存在文章。
    返回 (日报csv, 总表xlsx)
    """
    history_csv = Path(history_csv)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    history = load_history(history_csv)
    known_fps = {a.fingerprint for a in history}

    if deduper is not None:
        daily_articles = deduper.dedup(daily_articles)
    new_articles = [a for a in daily_articles if a.fingerprint not in known_fps]

    # 写日报
    daily_csv = output_dir / f"日报_{date}.csv"
    daily_xlsx = output_dir / f"日报_{date}.xlsx"
    write_csv(new_articles, daily_csv)
    write_xlsx(new_articles, daily_xlsx)

    # 合并进总表
    merged = history + new_articles
    write_csv(merged, history_csv)
    total_xlsx = output_dir / "具身智能行业资讯总表.xlsx"
    write_xlsx(merged, total_xlsx)

    return daily_csv, total_xlsx
