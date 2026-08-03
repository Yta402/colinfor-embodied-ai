# 开发者日志

> 具身智能行业资讯自动采集工作流
> 记录项目开发进度、关键决策与后续维护事项。

---

## 2026-08-03 — 项目启动

### 需求背景

领导需要每周看到具身智能行业最新资讯。经多轮沟通，最终确定需求：

- 采集源：微信公众号为主（纯自动抓取）
- 运行方式：GitHub Actions 每日定时（cron，早8点）
- 处理：DeepSeek API 做摘要 + 多标签归类
- 交付：Excel/CSV 表格，存入 GitHub 仓库（不做公众号/在线文档推送）
- 标签体系：前沿技术 / 行业知识 / 竞品动态 / 新品发布 / 商业融资 / 拆机实测（一文可多标签）

### 关键决策记录

| 决策点 | 结论 | 理由 |
|---|---|---|
| 采集方式 | 纯自动抓取，主备降级 | 用户选择，注意反爬失效风险 |
| 主源 | RSSHub 公众号路由 | 微信内容不开放公开接口 |
| 备源 | 搜狗微信 | RSSHub 失效时降级 |
| 补充源 | arXiv + 行业RSS | 保证信息覆盖度 |
| 归类模型 | DeepSeek API | 国内直连稳定、成本低 |
| 交付形式 | Excel/CSV 存仓库 | 用户明确不做推送 |
| 公众号名单 | 先用模板名单 | 后续可增删 |

### 模块规划

```
repo/
├─ .github/workflows/daily.yml     # 每日定时调度
├─ config/
│  ├─ accounts.yaml                # 目标公众号名单(模板)
│  └─ tags.yaml                    # 六类标签定义
├─ src/
│  ├─ collect/                     # 采集层(主备降级)
│  │  ├─ rsshub.py                 # 主源: RSSHub 公众号路由
│  │  ├─ sogou.py                  # 备源: 搜狗微信
│  │  └─ supplement.py             # 补充: arXiv + 行业RSS
│  ├─ process/                     # 处理层
│  │  ├─ dedup.py                  # 去重(标题/链接指纹)
│  │  ├─ classify.py               # DeepSeek 摘要+多标签
│  │  └─ enrich.py                 # 字段补齐
│  ├─ output/                      # 产出层
│  │  ├─ xlsx.py                   # 生成 Excel + CSV
│  │  └─ archive.py                # 历史合并
│  └─ notify.py                    # 失败告警(飞书/邮件)
├─ data/                           # 归档: 日报/周报/总表
└─ requirements.txt
```

### 风险与待办

- [ ] 模板公众号名单确定（具身智能/人形机器人/机器人/大模型行业号）
- [ ] DeepSeek API Key 配置为 GitHub Actions Secret
- [ ] 采集层反爬策略落地（随机UA、延时、验证码暂停告警）
- [ ] 主备降级链路测试

---

## 2026-08-03 — 首次实现完成

### 已交付

- 项目结构：`config/` `src/` `data/` `.github/workflows/`
- 配置：`accounts.yaml`（11个模板公众号名单）、`tags.yaml`（六类标签定义）
- 采集层：
  - `collect/base.py` — 公共工具（Article数据模型、随机UA会话、随机延时、指纹）
  - `collect/rsshub.py` — 主源 RSSHub 公众号路由，微信读书→搜狗两级降级
  - `collect/sogou.py` — 备源搜狗微信搜索，反爬验证码检测+告警
  - `collect/supplement.py` — 补充源 arXiv + 行业RSS
  - `collect/__init__.py` — 编排器，主备降级逻辑
- 处理层：
  - `process/dedup.py` — 指纹 + 标题相似度去重
  - `process/classify.py` — DeepSeek 摘要 + 多标签归类（一次调用完成）
  - `process/enrich.py` — 字段补齐 + 正文噪音清洗
- 产出层：
  - `output/table.py` — CSV(utf-8-sig) + XLSX 生成
  - `output/archive.py` — 增量合并进 history.csv + 总表
- `notify.py` — 飞书/邮件失败告警
- `main.py` — 主入口，串联流水线，支持 `--dry-run`
- `.github/workflows/daily.yml` — 每日 08:00(北京时间) cron 调度，自动提交数据
- `README.md`、`requirements.txt`、`.gitignore`、`DEVELOPMENT_LOG.md`

### 验证结果

- 全部模块 `compileall` 通过，导入无误
- 去重逻辑测试：3条 → 2条（重复项正确剔除）
- CSV / XLSX 生成、归档合并、历史读取：均通过
- dry-run 卡在外部网络请求（RSSHub/arXiv 公共实例响应慢），属预期

### 遗留事项 / 下一步

- [ ] 配置 GitHub Actions Secrets：`DEEPSEEK_API_KEY`（必需）、`RSSHUB_BASE`、告警渠道
- [ ] 建议自建 RSSHub 提高公众号路由稳定性
- [ ] 上线后用真实公众号做端到端验证（含搜狗降级链路）
- [ ] 本地 `.env` 加载支持（当前靠环境变量）
