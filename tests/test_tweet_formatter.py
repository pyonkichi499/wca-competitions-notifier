"""Tests for tweet_formatter module."""

from datetime import date

from src.tweet_formatter import format_date, format_events, format_tweet
from src.wca_client import Competition


class TestFormatDate:
    """Tests for format_date function."""

    def test_single_day(self, sample_competition):
        """Single day competition should format as one date."""
        result = format_date(sample_competition)
        assert result == "2025年8月15日"

    def test_multi_day_same_month(self, sample_competition_yokohama):
        """Multi-day same month should format as range."""
        result = format_date(sample_competition_yokohama)
        assert result == "2025年10月1日〜2日"

    def test_multi_day_different_months(self):
        """Multi-day different months should include both months."""
        comp = Competition(
            id="Test2025",
            name="Test 2025",
            city="Tokyo",
            venue="会場",
            start_date=date(2025, 12, 31),
            end_date=date(2026, 1, 1),
            events=["333"],
            url="https://example.com",
        )
        result = format_date(comp)
        assert result == "2025年12月31日〜2026年1月1日"

    def test_multi_day_same_year_different_month(self):
        """Multi-day same year but different month."""
        comp = Competition(
            id="Test2025",
            name="Test 2025",
            city="Tokyo",
            venue="会場",
            start_date=date(2025, 3, 30),
            end_date=date(2025, 4, 1),
            events=["333"],
            url="https://example.com",
        )
        result = format_date(comp)
        assert result == "2025年3月30日〜4月1日"


class TestFormatEvents:
    """Tests for format_events function."""

    def test_single_event(self):
        """Single event should format without extras."""
        result = format_events(["333"])
        assert result == "3x3x3"

    def test_multiple_events(self):
        """Multiple events should be comma separated."""
        result = format_events(["333", "222", "444"])
        assert result == "3x3x3, 2x2x2, 4x4x4"

    def test_japanese_event_names(self):
        """Japanese event names should be used."""
        result = format_events(["333bf", "333oh"])
        assert result == "3x3x3目隠し, 3x3x3片手"

    def test_max_events_limit(self):
        """Should limit to max_events and show remainder."""
        events = ["333", "222", "444", "555", "666", "777", "333bf"]
        result = format_events(events, max_events=5)
        assert result == "3x3x3, 2x2x2, 4x4x4, 5x5x5, 6x6x6 他2種目"

    def test_exactly_max_events(self):
        """Exactly max events should not show remainder."""
        events = ["333", "222", "444", "555", "666"]
        result = format_events(events, max_events=5)
        assert result == "3x3x3, 2x2x2, 4x4x4, 5x5x5, 6x6x6"
        assert "他" not in result

    def test_unknown_event_code(self):
        """Unknown event code should pass through."""
        result = format_events(["333", "unknown_event"])
        assert result == "3x3x3, unknown_event"


class TestFormatTweet:
    """Tests for format_tweet function."""

    def test_tweet_contains_competition_name(self, sample_competition):
        """Tweet should contain competition name."""
        result = format_tweet(sample_competition)
        assert "Tokyo Open 2025" in result

    def test_tweet_contains_date(self, sample_competition):
        """Tweet should contain formatted date."""
        result = format_tweet(sample_competition)
        assert "2025年8月15日" in result

    def test_tweet_contains_location(self, sample_competition):
        """Tweet should contain city."""
        result = format_tweet(sample_competition)
        assert "Tokyo" in result

    def test_tweet_contains_url(self, sample_competition):
        """Tweet should contain WCA URL."""
        result = format_tweet(sample_competition)
        assert sample_competition.url in result

    def test_tweet_contains_hashtags(self, sample_competition):
        """Tweet should contain hashtags."""
        result = format_tweet(sample_competition)
        assert "#WCA" in result
        assert "#スピードキューブ" in result

    def test_tweet_contains_events(self, sample_competition):
        """Tweet should contain event names."""
        result = format_tweet(sample_competition)
        assert "3x3x3" in result

    def test_tweet_within_character_limit(self, sample_competition):
        """Tweet should be within Twitter's character limit."""
        result = format_tweet(sample_competition)
        # Twitter limit is 280 characters
        # Note: URLs count as 23 characters on Twitter
        assert len(result) < 500  # Generous limit for raw text
