"""Format competition data into tweet text."""

from .config import EVENT_NAMES, TWEET_TEMPLATE
from .wca_client import Competition


def format_date(competition: Competition) -> str:
    """Format competition date(s) in Japanese format.

    Args:
        competition: The competition to format date for.

    Returns:
        Formatted date string (e.g., "2025年8月15日" or "2025年8月15日〜16日")
    """
    start = competition.start_date
    end = competition.end_date

    if start == end:
        return f"{start.year}年{start.month}月{start.day}日"
    elif start.year == end.year and start.month == end.month:
        return f"{start.year}年{start.month}月{start.day}日〜{end.day}日"
    elif start.year == end.year:
        return f"{start.year}年{start.month}月{start.day}日〜{end.month}月{end.day}日"
    else:
        return (
            f"{start.year}年{start.month}月{start.day}日"
            f"〜{end.year}年{end.month}月{end.day}日"
        )


def format_events(events: list[str], max_events: int = 5) -> str:
    """Format event codes into Japanese event names.

    Args:
        events: List of WCA event codes.
        max_events: Maximum number of events to display.

    Returns:
        Comma-separated string of event names.
    """
    event_names = []
    for event_code in events[:max_events]:
        name = EVENT_NAMES.get(event_code, event_code)
        event_names.append(name)

    result = ", ".join(event_names)

    if len(events) > max_events:
        result += f" 他{len(events) - max_events}種目"

    return result


def format_tweet(competition: Competition) -> str:
    """Format a competition into a tweet.

    Args:
        competition: The competition to format.

    Returns:
        Tweet text ready to post.
    """
    return TWEET_TEMPLATE.format(
        name=competition.name,
        date=format_date(competition),
        location=competition.city or "日本",
        events=format_events(competition.events),
        url=competition.url,
    )
