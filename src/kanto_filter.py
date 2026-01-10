"""Filter competitions by Kanto region."""

from .config import KANTO_KEYWORDS
from .wca_client import Competition


def is_kanto_competition(competition: Competition) -> bool:
    """Check if a competition is held in the Kanto region.

    Args:
        competition: The competition to check.

    Returns:
        True if the competition is in Kanto, False otherwise.
    """
    # Check city, venue, and competition name for Kanto keywords
    searchable_text = " ".join(
        [
            competition.city,
            competition.venue,
            competition.name,
        ]
    )

    for keyword in KANTO_KEYWORDS:
        if keyword.lower() in searchable_text.lower():
            return True

    return False


def filter_kanto_competitions(competitions: list[Competition]) -> list[Competition]:
    """Filter competitions to only include those in Kanto region.

    Args:
        competitions: List of competitions to filter.

    Returns:
        List of competitions in Kanto region.
    """
    return [comp for comp in competitions if is_kanto_competition(comp)]
