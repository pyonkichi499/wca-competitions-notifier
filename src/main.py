"""FastAPI application for WCA Kanto Notifier."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from .competition_tracker import CompetitionTracker
from .kanto_filter import filter_kanto_competitions
from .logger import get_logger, setup_logging
from .tweet_formatter import format_tweet
from .twitter_client import DryRunTwitterClient, TwitterClient
from .wca_client import fetch_upcoming_japan_competitions

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    setup_logging()
    logger.info("WCA Kanto Notifier starting...")
    yield
    logger.info("WCA Kanto Notifier shutting down...")


app = FastAPI(
    title="WCA Kanto Notifier",
    description="Twitter bot that notifies new WCA competitions in Kanto, Japan",
    version="0.1.0",
    lifespan=lifespan,
)


def get_twitter_client() -> TwitterClient:
    """Get the appropriate Twitter client based on environment."""
    dry_run = os.getenv("DRY_RUN", "false").lower() == "true"
    if dry_run:
        return DryRunTwitterClient()
    return TwitterClient()


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "WCA Kanto Notifier"}


@app.post("/notify")
async def notify():
    """Check for new competitions and post to Twitter.

    This is the main endpoint called by Cloud Scheduler.
    """
    try:
        # 1. Fetch upcoming Japan competitions
        logger.info("Fetching upcoming Japan competitions...")
        competitions = await fetch_upcoming_japan_competitions()
        logger.info("Found %d upcoming competitions in Japan", len(competitions))

        # 2. Filter for Kanto region
        kanto_competitions = filter_kanto_competitions(competitions)
        logger.info("Found %d competitions in Kanto region", len(kanto_competitions))

        # 3. Find new competitions
        tracker = CompetitionTracker()
        new_competitions = tracker.find_new_competitions(kanto_competitions)
        logger.info("Found %d new competitions to notify", len(new_competitions))

        if not new_competitions:
            return {
                "status": "ok",
                "message": "No new competitions to notify",
                "total_japan": len(competitions),
                "total_kanto": len(kanto_competitions),
                "new_competitions": 0,
            }

        # 4. Post to Twitter
        twitter = get_twitter_client()

        if not twitter.is_configured():
            raise HTTPException(
                status_code=500,
                detail="Twitter credentials not configured",
            )

        posted = []
        for comp in new_competitions:
            tweet_text = format_tweet(comp)
            logger.info("Posting tweet for: %s", comp.name)

            try:
                result = twitter.post_tweet(tweet_text)
                tracker.mark_as_notified(comp)
                posted.append(
                    {
                        "competition_id": comp.id,
                        "competition_name": comp.name,
                        "tweet_id": result.get("id"),
                    }
                )
            except Exception as e:
                logger.error("Failed to post tweet for %s: %s", comp.name, e)
                # Continue with other competitions even if one fails

        # 5. Save state
        tracker.save()
        logger.info("Successfully posted %d tweets", len(posted))

        return {
            "status": "ok",
            "message": f"Posted {len(posted)} new competition(s)",
            "total_japan": len(competitions),
            "total_kanto": len(kanto_competitions),
            "new_competitions": len(new_competitions),
            "posted": posted,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error during notification")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/competitions")
async def list_competitions():
    """List current Kanto competitions (for debugging)."""
    try:
        competitions = await fetch_upcoming_japan_competitions()
        kanto_competitions = filter_kanto_competitions(competitions)

        return {
            "total_japan": len(competitions),
            "total_kanto": len(kanto_competitions),
            "competitions": [
                {
                    "id": c.id,
                    "name": c.name,
                    "city": c.city,
                    "start_date": c.start_date.isoformat(),
                    "end_date": c.end_date.isoformat(),
                    "events": c.events,
                    "url": c.url,
                }
                for c in kanto_competitions
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/preview/{competition_id}")
async def preview_tweet(competition_id: str):
    """Preview the tweet for a specific competition."""
    try:
        competitions = await fetch_upcoming_japan_competitions()

        comp = next((c for c in competitions if c.id == competition_id), None)
        if not comp:
            raise HTTPException(status_code=404, detail="Competition not found")

        return {
            "competition_id": comp.id,
            "competition_name": comp.name,
            "tweet": format_tweet(comp),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
