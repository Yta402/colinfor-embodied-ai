"""失败告警：飞书机器人 / 邮件。

触发条件: 采集主备源全部失败、LLM 归类大面积失败、进程异常退出。
告警渠道通过环境变量配置，未配置时静默跳过（仅打印日志）。
"""

from __future__ import annotations

import os
import smtplib
from email.mime.text import MIMEText

import requests


class Notifier:
    """向配置的渠道发送告警。"""

    def __init__(self, feishu_webhook: str | None = None):
        self.feishu_webhook = feishu_webhook or os.getenv("FEISHU_WEBHOOK", "")

    def _feishu(self, title: str, content: str) -> None:
        payload = {
            "msg_type": "post",
            "content": {
                "post": {
                    "zh_cn": {
                        "title": title,
                        "content": [[{"tag": "text", "text": content}]],
                    }
                }
            },
        }
        resp = requests.post(self.feishu_webhook, json=payload, timeout=15)
        resp.raise_for_status()

    def _email(self, subject: str, body: str) -> None:
        smtp_host = os.getenv("SMTP_HOST", "")
        smtp_port = int(os.getenv("SMTP_PORT", "465"))
        smtp_user = os.getenv("SMTP_USER", "")
        smtp_pass = os.getenv("SMTP_PASS", "")
        mail_to = os.getenv("MAIL_TO", "")
        if not (smtp_host and smtp_user and smtp_pass and mail_to):
            return
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = smtp_user
        msg["To"] = mail_to
        with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=20) as server:
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, [mail_to], msg.as_string())

    def alert(self, title: str, content: str) -> None:
        """发送告警，任一渠道失败不影响其他/主流程。"""
        errors = []
        if self.feishu_webhook:
            try:
                self._feishu(title, content)
            except Exception as e:
                errors.append(f"feishu: {e}")
        try:
            self._email(title, content)
        except Exception as e:
            errors.append(f"email: {e}")
        if errors:
            print(f"[notify] 告警发送失败: {errors}")
