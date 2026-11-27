"""Outgoing email (P5.4). Locally it goes to the console; a real provider comes with deployment.

Only these three messages exist. A message carries a link with a one-time token, or nothing
secret at all (`account_exists`).
"""

import sys
from dataclasses import dataclass, field
from typing import Literal, Protocol

Kind = Literal["verify", "reset", "account_exists"]

SUBJECTS = {
    "verify": {"ar": "تأكيد بريدك الإلكتروني في Replora", "en": "Confirm your Replora email"},
    "reset": {"ar": "إعادة تعيين كلمة المرور في Replora", "en": "Reset your Replora password"},
    "account_exists": {"ar": "لديك حساب في Replora بالفعل",
                       "en": "You already have a Replora account"},
}  # fmt: skip


@dataclass(frozen=True)
class Message:
    to: str
    kind: Kind
    subject: str
    body: str


class Mailer(Protocol):
    def send(self, message: Message) -> None: ...


class ConsoleMailer:
    """The local sink: prints the message, link included, so a developer can click it."""

    def send(self, message: Message) -> None:
        print(f"--- email to {message.to}: {message.subject}\n{message.body}\n---",
              file=sys.stderr)  # fmt: skip


@dataclass
class Outbox:
    """A test sink that keeps every message."""

    sent: list[Message] = field(default_factory=list)

    def send(self, message: Message) -> None:
        self.sent.append(message)


def compose(to: str, kind: Kind, locale: str, link: str | None = None) -> Message:
    subject = SUBJECTS[kind]["ar" if locale == "ar" else "en"]
    return Message(to=to, kind=kind, subject=subject, body=link or subject)
