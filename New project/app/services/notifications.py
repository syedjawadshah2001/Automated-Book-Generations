from __future__ import annotations

import smtplib
from email.message import EmailMessage

import httpx

from app.config import Settings


class NotificationService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def send(self, subject: str, message: str) -> None:
        mode = self.settings.notification_mode.lower()
        if mode == "email":
            self._send_email(subject, message)
            return
        if mode == "teams":
            self._send_teams(subject, message)
            return
        print(f"[notification] {subject}: {message}")

    def _send_email(self, subject: str, message: str) -> None:
        email = EmailMessage()
        email["Subject"] = subject
        email["From"] = self.settings.smtp_username
        email["To"] = self.settings.notification_email_to
        email.set_content(message)

        with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port) as smtp:
            smtp.starttls()
            smtp.login(self.settings.smtp_username, self.settings.smtp_password)
            smtp.send_message(email)

    def _send_teams(self, subject: str, message: str) -> None:
        httpx.post(
            self.settings.teams_webhook_url,
            json={"text": f"**{subject}**\n\n{message}"},
            timeout=30.0,
        ).raise_for_status()
