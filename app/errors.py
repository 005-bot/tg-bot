"""Error hierarchy for the Telegram bot."""


class BotError(Exception):
    """Base exception with logging context."""

    def __init__(self, user_id=None, message=None):
        super().__init__(message)
        self.user_id = user_id
        self.context = {}


class UserInputError(BotError):
    """Invalid command/formatting errors."""


class APIError(BotError):
    """Telegram API failures with retry logic."""


class CriticalSystemError(BotError):
    """Requires immediate attention."""
