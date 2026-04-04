"""Tests for twitter_client module."""

from unittest.mock import MagicMock, patch

from src.twitter_client import DryRunTwitterClient, TwitterClient


class TestTwitterClient:
    """Tests for TwitterClient class."""

    def test_is_configured_all_credentials(self):
        """Should return True when all credentials are set."""
        client = TwitterClient(
            api_key="key",
            api_secret="secret",
            access_token="token",
            access_token_secret="token_secret",
        )
        assert client.is_configured() is True

    def test_is_configured_missing_api_key(self):
        """Should return False when API key is missing."""
        client = TwitterClient(
            api_key="",
            api_secret="secret",
            access_token="token",
            access_token_secret="token_secret",
        )
        assert client.is_configured() is False

    def test_is_configured_missing_all(self):
        """Should return False when all credentials are missing."""
        client = TwitterClient(
            api_key="",
            api_secret="",
            access_token="",
            access_token_secret="",
        )
        assert client.is_configured() is False

    def test_post_tweet_success(self):
        """Should post tweet and return response data."""
        client = TwitterClient(
            api_key="key",
            api_secret="secret",
            access_token="token",
            access_token_secret="token_secret",
        )

        mock_response = MagicMock()
        mock_response.data = {"id": "12345", "text": "Test tweet"}

        with patch("src.twitter_client.tweepy.Client") as mock_tweepy:
            mock_tweepy.return_value.create_tweet.return_value = mock_response

            result = client.post_tweet("Test tweet")

            assert result == {"id": "12345", "text": "Test tweet"}
            mock_tweepy.return_value.create_tweet.assert_called_once_with(
                text="Test tweet"
            )

    def test_client_is_cached(self):
        """Should reuse the same tweepy client instance."""
        client = TwitterClient(
            api_key="key",
            api_secret="secret",
            access_token="token",
            access_token_secret="token_secret",
        )

        with patch("src.twitter_client.tweepy.Client") as mock_tweepy:
            # First call creates client
            client._get_client()
            # Second call reuses client
            client._get_client()

            # Should only create one client
            assert mock_tweepy.call_count == 1


class TestDryRunTwitterClient:
    """Tests for DryRunTwitterClient class."""

    def test_post_tweet_returns_mock_data(self):
        """Should return mock response without actually posting."""
        client = DryRunTwitterClient()

        result = client.post_tweet("Test tweet content")

        assert result["id"] == "dry_run_tweet_id"
        assert result["text"] == "Test tweet content"

    def test_is_configured_always_true(self):
        """Should always return True for dry run client."""
        client = DryRunTwitterClient()
        assert client.is_configured() is True

    def test_is_configured_true_even_without_credentials(self):
        """Should return True even when no credentials provided."""
        client = DryRunTwitterClient(
            api_key="",
            api_secret="",
            access_token="",
            access_token_secret="",
        )
        assert client.is_configured() is True
