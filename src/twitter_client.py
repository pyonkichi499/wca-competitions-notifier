"""Twitter/X API client for posting tweets."""

import tweepy

from .config import (
    TWITTER_ACCESS_TOKEN,
    TWITTER_ACCESS_TOKEN_SECRET,
    TWITTER_API_KEY,
    TWITTER_API_SECRET,
)
from .logger import get_logger

logger = get_logger(__name__)


class TwitterClient:
    """Client for posting to Twitter/X."""

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        access_token: str | None = None,
        access_token_secret: str | None = None,
    ):
        """Initialize the Twitter client.

        Args:
            api_key: Twitter API key. Defaults to env var.
            api_secret: Twitter API secret. Defaults to env var.
            access_token: Twitter access token. Defaults to env var.
            access_token_secret: Twitter access token secret. Defaults to env var.
        """
        self.api_key = api_key or TWITTER_API_KEY
        self.api_secret = api_secret or TWITTER_API_SECRET
        self.access_token = access_token or TWITTER_ACCESS_TOKEN
        self.access_token_secret = access_token_secret or TWITTER_ACCESS_TOKEN_SECRET

        self._client: tweepy.Client | None = None

    def _get_client(self) -> tweepy.Client:
        """Get or create the tweepy client."""
        if self._client is None:
            self._client = tweepy.Client(
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret,
            )
        return self._client

    def post_tweet(self, text: str) -> dict:
        """Post a tweet.

        Args:
            text: The tweet text to post.

        Returns:
            Response data from Twitter API.

        Raises:
            tweepy.TweepyException: If the tweet fails to post.
        """
        client = self._get_client()
        response = client.create_tweet(text=text)
        return response.data

    def is_configured(self) -> bool:
        """Check if Twitter credentials are configured.

        Returns:
            True if all credentials are set, False otherwise.
        """
        return all(
            [
                self.api_key,
                self.api_secret,
                self.access_token,
                self.access_token_secret,
            ]
        )


class DryRunTwitterClient(TwitterClient):
    """Mock Twitter client for testing (doesn't actually post)."""

    def post_tweet(self, text: str) -> dict:
        """Log tweet instead of posting.

        Args:
            text: The tweet text to log.

        Returns:
            Mock response data.
        """
        logger.info("[DRY RUN] Would post tweet:\n%s", text)
        return {"id": "dry_run_tweet_id", "text": text}

    def is_configured(self) -> bool:
        """Always return True for dry run client."""
        return True
