#!/usr/bin/env python3
"""Local development script for testing the notifier."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.competition_tracker import CompetitionTracker, LocalStorage
from src.kanto_filter import filter_kanto_competitions
from src.logger import get_logger, setup_logging
from src.tweet_formatter import format_tweet
from src.twitter_client import DryRunTwitterClient
from src.wca_client import fetch_upcoming_japan_competitions

logger = get_logger(__name__)


async def main():
    """Run the notifier locally with dry-run mode."""
    setup_logging("INFO")

    logger.info("=" * 60)
    logger.info("WCA Kanto Notifier - Local Test Run")
    logger.info("=" * 60)

    # 1. Fetch competitions
    logger.info("[1/5] Fetching upcoming Japan competitions...")
    competitions = await fetch_upcoming_japan_competitions()
    logger.info("      Found %d upcoming competitions in Japan", len(competitions))

    # 2. Filter for Kanto
    logger.info("[2/5] Filtering for Kanto region...")
    kanto_competitions = filter_kanto_competitions(competitions)
    logger.info("      Found %d competitions in Kanto", len(kanto_competitions))

    if kanto_competitions:
        logger.info("      Kanto competitions:")
        for comp in kanto_competitions:
            logger.info("      - %s (%s, %s)", comp.name, comp.city, comp.start_date)

    # 3. Find new competitions
    logger.info("[3/5] Checking for new competitions...")
    tracker = CompetitionTracker(storage=LocalStorage())
    new_competitions = tracker.find_new_competitions(kanto_competitions)
    logger.info("      Found %d new competitions", len(new_competitions))

    if not new_competitions:
        logger.info("      No new competitions to notify.")
        logger.info("      (To reset, delete data/notified_competitions.json)")
        return

    # 4. Generate and show tweets
    logger.info("[4/5] Generating tweets (DRY RUN)...")
    twitter = DryRunTwitterClient()

    for comp in new_competitions:
        tweet_text = format_tweet(comp)
        twitter.post_tweet(tweet_text)
        tracker.mark_as_notified(comp)

    # 5. Save state
    logger.info("[5/5] Saving state...")
    tracker.save()
    logger.info("      State saved to data/notified_competitions.json")

    logger.info("=" * 60)
    logger.info("Done! In production, these tweets would be posted to Twitter.")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
