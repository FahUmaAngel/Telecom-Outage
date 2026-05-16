"""
Notification helpers for scraper health.

Optional integrations:
- Slack Incoming Webhook
- SMTP email

All configuration is via environment variables. If nothing is configured,
notifications are skipped.
"""

from __future__ import annotations

import json
import logging
import os
import smtplib
from dataclasses import dataclass
from datetime import datetime
from email.message import EmailMessage
from typing import Optional

import requests

logger = logging.getLogger(__name__)


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class AlertConfig:
    enabled: bool
    slack_webhook_url: Optional[str]
    discord_webhook_url: Optional[str]
    email_to: Optional[str]
    smtp_host: Optional[str]
    smtp_port: int
    smtp_user: Optional[str]
    smtp_password: Optional[str]
    smtp_from: Optional[str]
    smtp_tls: bool


def load_alert_config() -> AlertConfig:
    return AlertConfig(
        enabled=_env_bool("SCRAPER_ALERTS_ENABLED", default=True),
        slack_webhook_url=os.getenv("SLACK_WEBHOOK_URL") or None,
        discord_webhook_url=os.getenv("DISCORD_WEBHOOK_URL") or None,
        email_to=os.getenv("ALERT_EMAIL_TO") or None,
        smtp_host=os.getenv("SMTP_HOST") or None,
        smtp_port=int(os.getenv("SMTP_PORT") or "587"),
        smtp_user=os.getenv("SMTP_USER") or None,
        smtp_password=os.getenv("SMTP_PASSWORD") or None,
        smtp_from=os.getenv("SMTP_FROM") or None,
        smtp_tls=_env_bool("SMTP_TLS", default=True),
    )


def _fmt_dt(dt: Optional[datetime]) -> str:
    if not dt:
        return "—"
    try:
        return dt.isoformat()
    except Exception:
        return str(dt)


def notify_scraper_failure(
    operator: str,
    error_message: str,
    *,
    started_at: Optional[datetime] = None,
    finished_at: Optional[datetime] = None,
    retry_count: int = 0,
) -> None:
    """
    Best-effort failure notification. Never raises.
    """
    cfg = load_alert_config()
    if not cfg.enabled:
        return

    operator_norm = (operator or "unknown").upper()
    title = f"[Scraper Failed] {operator_norm}"
    body_lines = [
        f"Operator: {operator_norm}",
        f"Started: {_fmt_dt(started_at)}",
        f"Finished: {_fmt_dt(finished_at)}",
        f"Retries: {retry_count}",
        f"Error: {error_message}",
    ]
    text_body = "\n".join(body_lines)

    if cfg.slack_webhook_url:
        try:
            payload = {
                "text": title,
                "attachments": [
                    {
                        "color": "danger",
                        "text": f"```{text_body}```",
                    }
                ],
            }
            requests.post(
                cfg.slack_webhook_url,
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
        except Exception:
            logger.exception("Slack alert failed for %s", operator_norm)

    if cfg.discord_webhook_url:
        try:
            # Discord webhooks accept {"content": "..."} for a simple message.
            # Keep it compact; include details in a code block.
            payload = {"content": f"**{title}**\n```{text_body}```"}
            requests.post(
                cfg.discord_webhook_url,
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
        except Exception:
            logger.exception("Discord alert failed for %s", operator_norm)

    if cfg.smtp_host and cfg.email_to:
        try:
            msg = EmailMessage()
            msg["Subject"] = title
            msg["To"] = cfg.email_to
            msg["From"] = cfg.smtp_from or cfg.smtp_user or "scraper-alerts@localhost"
            msg.set_content(text_body)

            if cfg.smtp_tls:
                with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port, timeout=15) as smtp:
                    smtp.starttls()
                    if cfg.smtp_user and cfg.smtp_password:
                        smtp.login(cfg.smtp_user, cfg.smtp_password)
                    smtp.send_message(msg)
            else:
                with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port, timeout=15) as smtp:
                    if cfg.smtp_user and cfg.smtp_password:
                        smtp.login(cfg.smtp_user, cfg.smtp_password)
                    smtp.send_message(msg)
        except Exception:
            logger.exception("Email alert failed for %s", operator_norm)
