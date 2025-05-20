"""Core email handling functionality."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from imap_tools import MailBox, MailMessage


@dataclass
class Email:
    """Represents a processed email with essential information."""

    date: datetime
    from_: str
    subject: str
    size: int
    body: str
    is_human: bool = True  # Flag for human vs automated emails


class EmailHandler:
    """Handles email fetching and basic processing."""

    def __init__(self, host: str, user: str, password: str):
        self.host = host
        self.user = user
        self.password = password

    def fetch_emails(self, unread: bool = False, limit: int = 10) -> List[Email]:
        """Fetch emails from the mailbox."""
        criteria = "UNSEEN" if unread else "ALL"

        with MailBox(self.host).login(self.user, self.password) as mailbox:
            messages = list(mailbox.fetch(criteria, limit=limit, reverse=True))
            return [self._process_email(msg) for msg in messages]

    def _process_email(self, message: MailMessage) -> Email:
        """Process a raw email message into our Email dataclass."""
        return Email(
            date=message.date,
            from_=message.from_,
            subject=message.subject,
            size=message.size,
            body=message.text or message.html or "",
            is_human=self._is_human_email(message),
        )

    def _is_human_email(self, message: MailMessage) -> bool:
        """Determine if an email is from a human or automated system.

        This is a basic implementation that can be enhanced with more sophisticated
        detection methods in the future.
        """
        # Basic checks for automated emails
        automated_indicators = [
            "noreply@",
            "no-reply@",
            "donotreply@",
            "auto@",
            "automated@",
            "system@",
            "notification@",
        ]

        from_address = message.from_.lower()
        return not any(indicator in from_address for indicator in automated_indicators)
