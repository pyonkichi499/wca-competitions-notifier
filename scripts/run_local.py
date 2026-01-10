#!/usr/bin/env python3
"""Local development script for testing the notifier."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.competition_tracker import CompetitionTracker, LocalStorage
from src.kanto_filter import filter_kanto_competitions
from src.tweet_formatter import format_tweet
from src.twitter_client import DryRunTwitterClient
from src.wca_client import fetch_upcoming_japan_competitions


async def main():
    """Run the notifier locally with dry-run mode."""
    print("=" * 60)
    print("WCA Kanto Notifier - Local Test Run")
    print("=" * 60)

    # 1. Fetch competitions
    print("\n[1/5] Fetching upcoming Japan competitions...")
    competitions = await fetch_upcoming_japan_competitions()
    print(f"      Found {len(competitions)} upcoming competitions in Japan")

    # 2. Filter for Kanto
    print("\n[2/5] Filtering for Kanto region...")
    kanto_competitions = filter_kanto_competitions(competitions)
    print(f"      Found {len(kanto_competitions)} competitions in Kanto")

    if kanto_competitions:
        print("\n      Kanto competitions:")
        for comp in kanto_competitions:
            print(f"      - {comp.name} ({comp.city}, {comp.start_date})")

    # 3. Find new competitions
    print("\n[3/5] Checking for new competitions...")
    tracker = CompetitionTracker(storage=LocalStorage())
    new_competitions = tracker.find_new_competitions(kanto_competitions)
    print(f"      Found {len(new_competitions)} new competitions")

    if not new_competitions:
        print("\n      No new competitions to notify.")
        print("      (To reset, delete data/notified_competitions.json)")
        return

    # 4. Generate and show tweets
    print("\n[4/5] Generating tweets (DRY RUN)...")
    twitter = DryRunTwitterClient()

    for comp in new_competitions:
        tweet_text = format_tweet(comp)
        twitter.post_tweet(tweet_text)
        tracker.mark_as_notified(comp)

    # 5. Save state
    print("\n[5/5] Saving state...")
    tracker.save()
    print("      State saved to data/notified_competitions.json")

    print("\n" + "=" * 60)
    print("Done! In production, these tweets would be posted to Twitter.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
