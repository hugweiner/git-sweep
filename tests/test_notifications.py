"""Tests for git_sweep.notifications."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from git_sweep.notifications import (
    NotificationConfig,
    NotificationResult,
    send_notification,
    _send_email,
    _send_webhook,
)


def _cfg(**kwargs) -> NotificationConfig:
    defaults = dict(enabled=True, recipients=["dev@example.com"])
    defaults.update(kwargs)
    return NotificationConfig(**defaults)


def test_send_notification_disabled_returns_none():
    cfg = _cfg(enabled=False)
    result = send_notification(cfg, "subject", "body")
    assert result is None


def test_send_notification_unknown_method():
    cfg = _cfg(method="slack")
    result = send_notification(cfg, "subject", "body")
    assert result is not None
    assert result.sent is False
    assert "unknown" in (result.error or "")


def test_send_email_success():
    cfg = _cfg(method="email", smtp_host="localhost", smtp_port=25)
    mock_smtp = MagicMock()
    mock_smtp.__enter__ = lambda s: s
    mock_smtp.__exit__ = MagicMock(return_value=False)
    with patch("smtplib.SMTP", return_value=mock_smtp):
        result = _send_email(cfg, "Test Subject", "Hello")
    assert result.sent is True
    assert result.method == "email"
    assert result.error is None


def test_send_email_failure():
    cfg = _cfg(method="email")
    with patch("smtplib.SMTP", side_effect=OSError("connection refused")):
        result = _send_email(cfg, "subj", "body")
    assert result.sent is False
    assert "connection refused" in (result.error or "")


def test_send_webhook_success():
    cfg = _cfg(method="webhook", webhook_url="http://hooks.example.com/sweep")
    mock_resp = MagicMock()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_open:
        result = _send_webhook(cfg, "subj", "body")
        called_req = mock_open.call_args[0][0]
        payload = json.loads(called_req.data)
        assert payload["subject"] == "subj"
    assert result.sent is True
    assert result.method == "webhook"


def test_send_webhook_failure():
    cfg = _cfg(method="webhook", webhook_url="http://bad.example.com")
    with patch("urllib.request.urlopen", side_effect=OSError("timeout")):
        result = _send_webhook(cfg, "subj", "body")
    assert result.sent is False
    assert "timeout" in (result.error or "")


def test_send_notification_routes_to_email():
    cfg = _cfg(method="email")
    with patch("git_sweep.notifications._send_email") as mock_fn:
        mock_fn.return_value = NotificationResult(sent=True, method="email")
        result = send_notification(cfg, "s", "b")
    mock_fn.assert_called_once_with(cfg, "s", "b")
    assert result.sent is True


def test_send_notification_routes_to_webhook():
    cfg = _cfg(method="webhook", webhook_url="http://x.example.com")
    with patch("git_sweep.notifications._send_webhook") as mock_fn:
        mock_fn.return_value = NotificationResult(sent=True, method="webhook")
        result = send_notification(cfg, "s", "b")
    mock_fn.assert_called_once_with(cfg, "s", "b")
    assert result.sent is True
