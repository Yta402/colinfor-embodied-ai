"""主入口：串联采集 → 去重 → 通俗解读/归类 → 产出 → 归档。

用法:
    python -m src.main                # 使用默认配置
    python -m src.main --dry-run      # 只采集不写文件
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

from .collect import CollectorOrchestrator
from .notify import Notifier
from .output.archive import merge_into_history
from .process.classify import LLMClassifier
from .process.dedup import Deduper
from .process.enrich import Enricher

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("main")

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
HISTORY_CSV = DATA_DIR / "history.csv"


def run(dry_run: bool = False) -> int:
    today = datetime.now().strftime("%Y-%m-%d")
    notifier = Notifier()
    report: dict = {}

    try:
        # 1. 采集
        logger.info("开始采集...")
        orchestrator = CollectorOrchestrator()
        articles = orchestrator.collect()
        report = orchestrator.report
        collected = len(articles)
        logger.info("采集到 %d 条", collected)

        if not articles:
            notifier.alert("具身智能采集：无结果", "RSS 源均未采集到相关文章，请检查源配置或关键词。")
            return 1

        # 2. 处理
        logger.info("清洗字段...")
        articles = Enricher().enrich(articles, today)

        logger.info("去重...")
        articles = Deduper().dedup(articles)
        logger.info("去重后 %d 条", len(articles))

        if not articles:
            notifier.alert("具身智能采集：全部重复", "当日无新增文章。")
            return 0

        logger.info("LLM 通俗解读/归类...")
        classifier = LLMClassifier()
        articles = classifier.classify_many(articles)
        tagged = sum(1 for a in articles if a.tags)
        logger.info("解读完成，%d/%d 带标签", tagged, len(articles))

        # 3. 产出
        if dry_run:
            logger.info("dry-run 模式，跳过写文件。")
            for a in articles[:10]:
                logger.info("  - [%s] %s tags=%s", a.account, a.title, a.tags)
            return 0

        daily_csv, total_xlsx = merge_into_history(articles, HISTORY_CSV, DATA_DIR, today)
        logger.info("日报已生成: %s", daily_csv)
        logger.info("总表已更新: %s", total_xlsx)

        # 4. 状态记录（供 workflow 后续步骤读取）
        status = {
            "date": today,
            "collected": collected,
            "deduped": len(articles),
            "tagged": tagged,
            "report": report,
        }
        import json

        with open(DATA_DIR / "last_run.json", "w", encoding="utf-8") as f:
            json.dump(status, f, ensure_ascii=False, indent=2)
        return 0

    except Exception as e:
        logger.exception("运行失败")
        notifier.alert("具身智能采集：运行失败", f"{type(e).__name__}: {e}")
        return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="具身智能行业资讯采集工作流")
    parser.add_argument("--dry-run", action="store_true", help="只采集处理，不写文件")
    args = parser.parse_args(argv)
    return run(dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
