# app/interfaces/providers/email_sender.py
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class EmailSenderImpl:
    """Email sender implementation using Resend API.

    Docs: https://resend.com/docs/api-reference/emails/send-email
    """

    def __init__(self, settings: Any):
        self.settings = settings
        self._logger = logger.getChild(self.__class__.__name__)
        self._logger.debug("EmailSenderImpl initialized")

    async def send(self, to: str, subject: str, html: str) -> None:
        """Send an email using the Resend API.

        Args:
            to: Recipient email address
            subject: Email subject
            html: Email content in HTML format
        """
        self._logger.info(
            "Preparing to send email",
            extra={"to": to, "subject": subject, "email_length": len(html)},
        )

        if not getattr(self.settings, "RESEND_API_KEY", None):
            error_msg = "RESEND_API_KEY not configured in Settings"
            self._logger.error(error_msg)
            raise RuntimeError(error_msg)

        url = "https://api.resend.com/emails"
        from_email = getattr(
            self.settings, "EMAIL_FROM", "quality-alerts@paperperu.com"
        )
        payload = {
            "from": from_email,
            "to": [to],
            "subject": subject,
            "html": html,
        }

        headers = {
            "Authorization": f"Bearer {self.settings.RESEND_API_KEY}",
            "Content-Type": "application/json",
        }

        self._logger.debug(
            "Sending email via Resend API",
            extra={
                "to": to,
                "from": from_email,
                "subject": subject,
                "endpoint": url,
                "content_length": len(html),
            },
        )

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()

                self._logger.info(
                    "Email sent successfully",
                    extra={
                        "to": to,
                        "subject": subject,
                        "status_code": response.status_code,
                        "response": response.json(),
                    },
                )
                return response.json()

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error occurred: {e!s}"
            self._logger.error(
                error_msg,
                extra={
                    "status_code": e.response.status_code,
                    "response": e.response.text,
                    "request_url": str(e.request.url),
                },
                exc_info=True,
            )
            raise

        except httpx.RequestError as e:
            error_msg = f"Request error occurred: {e!s}"
            self._logger.error(
                error_msg,
                extra={"request": str(e.request) if hasattr(e, "request") else None},
                exc_info=True,
            )
            raise

        except Exception as e:
            error_msg = f"Unexpected error sending email: {e!s}"
            self._logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg) from e
