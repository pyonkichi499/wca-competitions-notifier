"""Tests for wca_client module."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.wca_client import Competition, fetch_japan_competitions


class TestCompetition:
    """Tests for Competition dataclass."""

    def test_from_api_response(self, sample_api_response):
        """Should create Competition from API response."""
        comp = Competition.from_api_response(sample_api_response)

        assert comp.id == "TokyoSpring2025"
        assert comp.name == "Tokyo Spring 2025"
        assert comp.city == "Tokyo"
        assert comp.venue == "新宿区民センター"
        assert comp.start_date == date(2025, 4, 1)
        assert comp.end_date == date(2025, 4, 1)
        assert comp.events == ["333", "222", "pyram"]
        assert "TokyoSpring2025" in comp.url

    def test_from_api_response_missing_optional_fields(self):
        """Should handle missing optional fields."""
        data = {
            "id": "Test2025",
            "name": "Test 2025",
            "date": {
                "from": "2025-01-01",
                "till": "2025-01-01",
            },
        }

        comp = Competition.from_api_response(data)

        assert comp.id == "Test2025"
        assert comp.city == ""
        assert comp.venue == ""
        assert comp.events == []

    def test_from_api_response_missing_required_fields(self):
        """Should raise error for missing required fields."""
        data = {
            "name": "Test 2025",
            # missing id and date
        }

        with pytest.raises(KeyError):
            Competition.from_api_response(data)


class TestFetchJapanCompetitions:
    """Tests for fetch_japan_competitions function."""

    @pytest.mark.asyncio
    async def test_fetch_success(self, sample_api_response):
        """Should fetch and parse competitions successfully."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"items": [sample_api_response]}

        with patch("src.wca_client.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_instance

            result = await fetch_japan_competitions()

            assert len(result) == 1
            assert result[0].id == "TokyoSpring2025"

    @pytest.mark.asyncio
    async def test_fetch_empty_response(self):
        """Should handle empty response."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"items": []}

        with patch("src.wca_client.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_instance

            result = await fetch_japan_competitions()

            assert result == []

    @pytest.mark.asyncio
    async def test_fetch_skips_malformed_data(self, sample_api_response):
        """Should skip malformed competition data and continue."""
        malformed = {"name": "Bad Data"}  # missing required fields

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "items": [malformed, sample_api_response]
        }

        with patch("src.wca_client.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_instance

            result = await fetch_japan_competitions()

            # Should have parsed 1 valid competition, skipped 1 malformed
            assert len(result) == 1
            assert result[0].id == "TokyoSpring2025"
