"""Tests for kanto_filter module."""

from datetime import date

import pytest

from src.kanto_filter import filter_kanto_competitions, is_kanto_competition
from src.wca_client import Competition


class TestIsKantoCompetition:
    """Tests for is_kanto_competition function."""

    def test_tokyo_competition(self, sample_competition):
        """Tokyo competitions should be detected as Kanto."""
        assert is_kanto_competition(sample_competition) is True

    def test_yokohama_competition(self, sample_competition_yokohama):
        """Yokohama competitions should be detected as Kanto."""
        assert is_kanto_competition(sample_competition_yokohama) is True

    def test_chiba_competition(self, sample_competition_chiba):
        """Chiba competitions should be detected as Kanto."""
        assert is_kanto_competition(sample_competition_chiba) is True

    def test_osaka_competition(self, sample_competition_osaka):
        """Osaka competitions should NOT be detected as Kanto."""
        assert is_kanto_competition(sample_competition_osaka) is False

    def test_saitama_in_city(self):
        """Saitama in city name should be detected as Kanto."""
        comp = Competition(
            id="SaitamaOpen2025",
            name="Open 2025",
            city="Saitama",
            venue="会場",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 1),
            events=["333"],
            url="https://example.com",
        )
        assert is_kanto_competition(comp) is True

    def test_kanto_in_name(self):
        """'Kanto' in competition name should be detected as Kanto."""
        comp = Competition(
            id="KantoOpen2025",
            name="Kanto Open 2025",
            city="Unknown",
            venue="会場",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 1),
            events=["333"],
            url="https://example.com",
        )
        assert is_kanto_competition(comp) is True

    def test_japanese_tokyo_in_venue(self):
        """Japanese '東京' in venue should be detected as Kanto."""
        comp = Competition(
            id="Test2025",
            name="Test 2025",
            city="Unknown",
            venue="東京都民センター",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 1),
            events=["333"],
            url="https://example.com",
        )
        assert is_kanto_competition(comp) is True

    def test_ibaraki_competition(self):
        """Ibaraki should be detected as Kanto."""
        comp = Competition(
            id="IbarakiOpen2025",
            name="Ibaraki Open 2025",
            city="Ibaraki",
            venue="茨城県民ホール",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 1),
            events=["333"],
            url="https://example.com",
        )
        assert is_kanto_competition(comp) is True

    def test_case_insensitive(self):
        """Keyword matching should be case insensitive."""
        comp = Competition(
            id="Test2025",
            name="Test 2025",
            city="TOKYO",
            venue="会場",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 1),
            events=["333"],
            url="https://example.com",
        )
        assert is_kanto_competition(comp) is True


class TestFilterKantoCompetitions:
    """Tests for filter_kanto_competitions function."""

    def test_filter_mixed_competitions(
        self,
        sample_competition,
        sample_competition_osaka,
        sample_competition_yokohama,
    ):
        """Should filter only Kanto competitions from a mixed list."""
        competitions = [
            sample_competition,  # Tokyo - Kanto
            sample_competition_osaka,  # Osaka - Not Kanto
            sample_competition_yokohama,  # Yokohama - Kanto
        ]

        result = filter_kanto_competitions(competitions)

        assert len(result) == 2
        assert sample_competition in result
        assert sample_competition_yokohama in result
        assert sample_competition_osaka not in result

    def test_filter_empty_list(self):
        """Should return empty list for empty input."""
        result = filter_kanto_competitions([])
        assert result == []

    def test_filter_no_kanto(self, sample_competition_osaka):
        """Should return empty list when no Kanto competitions."""
        result = filter_kanto_competitions([sample_competition_osaka])
        assert result == []

    def test_filter_all_kanto(
        self,
        sample_competition,
        sample_competition_yokohama,
        sample_competition_chiba,
    ):
        """Should return all competitions when all are Kanto."""
        competitions = [
            sample_competition,
            sample_competition_yokohama,
            sample_competition_chiba,
        ]

        result = filter_kanto_competitions(competitions)

        assert len(result) == 3
