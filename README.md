# 具身智能行业资讯收集工作流

收集具身智能行业优质公众号文章**链接**，简单归类（六类标签）后整理进 Excel 表格，供领导每周查看。**本项目不发布任何内容，只产出表格。**

## 快速开始

```bash
pip install -r requirements.txt

# 需先设置 API Key
export DEEPSEEK_API_KEY=sk-xxx

# 本地跑一次
python -m src.main
```

## 配置

- `config/accounts.yaml` — 目标公众号名单（模板，可增删）
- `config/tags.yaml` — 六类标签定义：前沿技术 / 行业知识 / 竞品动态 / 新品发布 / 商业融资 / 拆机实测

## GitHub Actions Secrets

在仓库 Settings → Secrets and variables → Actions 配置：

| Secret | 必填 | 说明 |
|---|---|---|
| `DEEPSEEK_API_KEY` | 是 | DeepSeek API Key |
| `DEEPSEEK_MODEL` | 否 | DeepSeek 模型名，默认 `deepseek-v4-flash` |
| `RSSHUB_BASE` | 否 | RSSHub 地址，默认 `https://rsshub.app`，建议自建 |
| `FEISHU_WEBHOOK` | 否 | 飞书机器人 webhook，失败告警 |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASS` / `MAIL_TO` | 否 | 邮件告警 |

## 输出

- `data/日报_YYYY-MM-DD.csv` / `.xlsx` — 每日新增
- `data/history.csv` — 历史累计（增量合并）
- `data/具身智能行业资讯总表.xlsx` — 全量总表

## 采集降级策略

1. 主源 RSSHub 公众号路由
2. 主源失败/为空 → 搜狗微信按关键词
3. 始终补充 arXiv + 行业 RSS

## 开发日志

见 [DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md)
