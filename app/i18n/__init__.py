import locale
from datetime import datetime


def format_date_ru(date: datetime) -> str:
    """Format a single date with Russian locale.

    Args:
        date: Datetime object to format

    Returns:
        String with formatted date in Russian locale
    """
    current_locale = locale.getlocale()
    try:
        locale.setlocale(locale.LC_TIME, "ru_RU.UTF-8")
        return date.strftime("%d %B %H-%M").lower()
    finally:
        locale.setlocale(locale.LC_TIME, current_locale)
