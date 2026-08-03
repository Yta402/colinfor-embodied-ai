# 具身智能行业资讯收集工作流

采集机器人/具身智能行业**通俗报道**（行业媒体 RSS），按关键词过滤，LLM 转写成领导能看懂的解读并归类（六类标签），整理进 Excel 表格。**本项目不发布任何内容，只产出表格。**

## 快速开始

```bash
pip install -r requirements.txt

# 需先设置 API Key
export DEEPSEEK_API_KEY=sk-xxx

# 本地跑一次
python -m src.main

# 只采集处理不写文件
python -m src.main --dry-run
```

## 配置

- `config/sources.yaml` — 行业媒体 RSS 源名单（可增删，需实测可用）
- `config/keywords.yaml` — 关键词过滤（灵巧手/直驱/腱绳/伺服电缸/人形机器人等，命中任一保留）
- `config/tags.yaml` — 六类标签定义：前沿技术 / 行业知识 / 竞品动态 / 新品发布 / 商业融资 / 拆机实测

## GitHub Actions Secrets

在仓库 Settings → Secrets and variables → Actions 配置：

| Secret | 必填 | 说明 |
|---|---|---|
| `DEEPSEEK_API_KEY` | 是 | DeepSeek API Key |
| `DEEPSEEK_MODEL` | 否 | DeepSeek 模型名，默认 `deepseek-v4-flash` |
| `FEISHU_WEBHOOK` | 否 | 飞书机器人 webhook，失败告警 |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASS` / `MAIL_TO` | 否 | 邮件告警 |

## 输出

- `data/日报_YYYY-MM-DD.csv` / `.xlsx` — 每日新增
- `data/history.csv` — 历史累计（增量合并）
- `data/具身智能行业资讯总表.xlsx` — 全量总表

## 采集源现状（2026-08-03 实测）

已实测可用的 RSS 源：

- IEEE Spectrum Robotics
- InfoQ 机器人
- 36氪
- 量子位
- 极客公园
- TechCrunch AI
- VentureBeat AI
- The Verge AI

已放弃：公众号（反爬+无付费）、arXiv（领导需通俗报道非论文）。

## 开发日志

见 [DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md)
