"""Pytest configuration and fixtures."""

from datetime import date

import pytest

from src.wca_client import Competition


@pytest.fixture
def sample_competition() -> Competition:
    """Create a sample competition for testing."""
    return Competition(
        id="TokyoOpen2025",
        name="Tokyo Open 2025",
        city="Tokyo",
        venue="渋谷区民センター",
        start_date=date(2025, 8, 15),
        end_date=date(2025, 8, 15),
        events=["333", "222", "444", "333oh", "pyram"],
        url="https://www.worldcubeassociation.org/competitions/TokyoOpen2025",
    )


@pytest.fixture
def sample_competition_osaka() -> Competition:
    """Create a sample Osaka competition (not Kanto)."""
    return Competition(
        id="OsakaOpen2025",
        name="Osaka Open 2025",
        city="Osaka",
        venue="大阪市民ホール",
        start_date=date(2025, 9, 1),
        end_date=date(2025, 9, 1),
        events=["333", "222"],
        url="https://www.worldcubeassociation.org/competitions/OsakaOpen2025",
    )


@pytest.fixture
def sample_competition_yokohama() -> Competition:
    """Create a sample Yokohama competition (Kanto)."""
    return Competition(
        id="YokohamaOpen2025",
        name="Yokohama Open 2025",
        city="Yokohama",
        venue="横浜市民ホール",
        start_date=date(2025, 10, 1),
        end_date=date(2025, 10, 2),
        events=["333", "222", "444", "555", "666", "777", "333bf"],
        url="https://www.worldcubeassociation.org/competitions/YokohamaOpen2025",
    )


@pytest.fixture
def sample_competition_chiba() -> Competition:
    """Create a sample Chiba competition (Kanto)."""
    return Competition(
        id="ChibaOpen2025",
        name="Chiba Open 2025",
        city="Chiba",
        venue="千葉市民会館",
        start_date=date(2025, 11, 15),
        end_date=date(2025, 11, 15),
        events=["333"],
        url="https://www.worldcubeassociation.org/competitions/ChibaOpen2025",
    )


@pytest.fixture
def sample_api_response() -> dict:
    """Sample WCA API response data."""
    return {
        "id": "TokyoSpring2025",
        "name": "Tokyo Spring 2025",
        "city": "Tokyo",
        "venue": "新宿区民センター",
        "date": {
            "from": "2025-04-01",
            "till": "2025-04-01",
        },
        "events": ["333", "222", "pyram"],
    }
