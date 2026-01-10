"""WCA API client for fetching competition data."""

from dataclasses import dataclass
from datetime import date

import httpx

from .config import WCA_JAPAN_COMPETITIONS_URL
from .logger import get_logger

logger = get_logger(__name__)


@dataclass
class Competition:
    """Represents a WCA competition."""

    id: str
    name: str
    city: str
    venue: str
    start_date: date
    end_date: date
    events: list[str]
    url: str

    @classmethod
    def from_api_response(cls, data: dict) -> "Competition":
        """Create a Competition from WCA API response data."""
        return cls(
            id=data["id"],
            name=data["name"],
            city=data.get("city", ""),
            venue=data.get("venue", ""),
            start_date=date.fromisoformat(data["date"]["from"]),
            end_date=date.fromisoformat(data["date"]["till"]),
            events=data.get("events", []),
            url=f"https://www.worldcubeassociation.org/competitions/{data['id']}",
        )


async def fetch_japan_competitions() -> list[Competition]:
    """Fetch all Japanese competitions from WCA API.

    Returns:
        List of Competition objects for Japan.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(WCA_JAPAN_COMPETITIONS_URL, timeout=30.0)
        response.raise_for_status()
        data = response.json()

    competitions = []
    for item in data.get("items", []):
        try:
            comp = Competition.from_api_response(item)
            competitions.append(comp)
        except (KeyError, ValueError) as e:
            logger.warning("Skipping malformed competition data: %s", e)
            continue

    return competitions


async def fetch_upcoming_japan_competitions() -> list[Competition]:
    """Fetch upcoming Japanese competitions (not yet ended).

    Returns:
        List of upcoming Competition objects for Japan.
    """
    competitions = await fetch_japan_competitions()
    today = date.today()

    return [comp for comp in competitions if comp.end_date >= today]
