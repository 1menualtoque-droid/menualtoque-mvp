from datetime import datetime
from pathlib import Path
from typing import Any

import resend
from jinja2 import Environment, FileSystemLoader

from app.frameworks.settings import Settings

# Initialize settings
settings = Settings()

# Configure Jinja2 environment
template_dir = Path(__file__).parent / ".." / "templates"
env = Environment(loader=FileSystemLoader(template_dir))

# Initialize Resend client
resend.api_key = settings.RESEND_API_KEY


async def send_verification_email(
    email_to: str,
    username: str,
    verification_url: str,
) -> dict[str, Any]:
    """Send a verification email to the user.

    Args:
        email_to: Recipient's email address
        username: Recipient's username
        verification_url: The URL for email verification

    Returns:
        dict: Response from the email service
    """
    # Load and render the email template
    template = env.get_template("emails/verification_email.html")
    html_content = template.render(
        user_name=username, verification_url=verification_url, now=datetime.now()
    )

    # Send the email using Resend
    try:
        params = {
            "from": f"Fitsuyo <{settings.EMAIL_FROM}>",
            "to": [email_to],
            "subject": "Verifica tu Correo Electrónico - Fitsuyo",
            "html": html_content,
        }

        response = resend.Emails.send(params)
        return {"status": "success", "data": response}

    except Exception as e:
        return {"status": "error", "message": str(e)}


async def send_password_reset_email(
    email_to: str,
    username: str,
    reset_url: str,
) -> dict[str, Any]:
    """Send a password reset email to the user.

    Args:
        email_to: Recipient's email address
        username: Recipient's username
        reset_url: The URL for password reset

    Returns:
        dict: Response from the email service
    """
    # Load and render the email template
    template = env.get_template("emails/password_reset_email.html")
    html_content = template.render(
        user_name=username, reset_url=reset_url, now=datetime.now()
    )

    # Send the email using Resend
    try:
        params = {
            "from": f"Fitsuyo <{settings.EMAIL_FROM}>",
            "to": [email_to],
            "subject": "Recupera tu Contraseña - Fitsuyo",
            "html": html_content,
        }

        response = resend.Emails.send(params)
        return {"status": "success", "data": response}

    except Exception as e:
        return {"status": "error", "message": str(e)}


# Example usage:
# await send_verification_email("user@example.com", "John", "https://yourapp.com/verify?token=abc123")
# await send_password_reset_email("user@example.com", "John", "https://yourapp.com/reset?token=abc123")
