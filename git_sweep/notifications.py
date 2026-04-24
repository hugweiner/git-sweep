"""Notification support for git-sweep sweep results."""
from __future__ import annotations

import smtplib
import json
from dataclasses import dataclass, field
from email.message import EmailMessage
from typing import Optional


@dataclass
class NotificationConfig:
    enabled: bool = False
    method: str = "email"  # "email" | "webhook"
    recipients: list[str] = field(default_factory=list)
    smtp_host: str = "localhost"
    smtp_port: int = 25
    webhook_url: str = ""
    from_address: str = "git-sweep@localhost"


@dataclass
class NotificationResult:
    sent: bool
    method: str
    error: Optional[str] = None


def _send_email(cfg: NotificationConfig, subject: str, body: str) -> NotificationResult:
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = cfg.from_address
        msg["To"] = ", ".join(cfg.recipients)
        msg.set_content(body)
        with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port, timeout=10) as server:
            server.send_message(msg)
        return NotificationResult(sent=True, method="email")
    except Exception as exc:  # noqa: BLE001
        return NotificationResult(sent=False, method="email", error=str(exc))


def _send_webhook(cfg: NotificationConfig, subject: str, body: str) -> NotificationResult:
    try:
        import urllib.request

        payload = json.dumps({"subject": subject, "body": body}).encode()
        req = urllib.request.Request(
            cfg.webhook_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10):
            pass
        return NotificationResult(sent=True, method="webhook")
    except Exception as exc:  # noqa: BLE001
        return NotificationResult(sent=False, method="webhook", error=str(exc))


def send_notification(
    cfg: NotificationConfig, subject: str, body: str
) -> Optional[NotificationResult]:
    """Dispatch a notification according to *cfg*. Returns None when disabled."""
    if not cfg.enabled:
        return None
    if cfg.method == "email":
        return _send_email(cfg, subject, body)
    if cfg.method == "webhook":
        return _send_webhook(cfg, subject, body)
    return NotificationResult(sent=False, method=cfg.method, error="unknown method")
