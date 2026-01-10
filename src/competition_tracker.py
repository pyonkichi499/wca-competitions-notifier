"""Track notified competitions to avoid duplicates."""

import json
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path

from .config import ENV, GCS_BUCKET_NAME, GCS_STATE_FILE, LOCAL_STATE_FILE
from .wca_client import Competition


class StorageBase(ABC):
    """Abstract base class for competition state storage."""

    @abstractmethod
    def load_notified_ids(self) -> set[str]:
        """Load the set of notified competition IDs.

        Returns:
            Set of competition IDs that have been notified.
        """
        pass

    @abstractmethod
    def save_notified_ids(self, ids: set[str]) -> None:
        """Save the set of notified competition IDs.

        Args:
            ids: Set of competition IDs to save.
        """
        pass


class LocalStorage(StorageBase):
    """Local file-based storage for development."""

    def __init__(self, file_path: str | None = None):
        """Initialize local storage.

        Args:
            file_path: Path to the state file. Defaults to config value.
        """
        self.file_path = Path(file_path or LOCAL_STATE_FILE)

    def load_notified_ids(self) -> set[str]:
        """Load notified IDs from local JSON file."""
        if not self.file_path.exists():
            return set()

        try:
            with open(self.file_path) as f:
                data = json.load(f)
                return set(data.get("notified_competitions", []))
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: Failed to load state file: {e}")
            return set()

    def save_notified_ids(self, ids: set[str]) -> None:
        """Save notified IDs to local JSON file."""
        # Ensure parent directory exists
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "notified_competitions": sorted(ids),
        }

        with open(self.file_path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


class CloudStorage(StorageBase):
    """Google Cloud Storage for production."""

    def __init__(self, bucket_name: str | None = None, file_name: str | None = None):
        """Initialize Cloud Storage.

        Args:
            bucket_name: GCS bucket name. Defaults to config value.
            file_name: State file name. Defaults to config value.
        """
        self.bucket_name = bucket_name or GCS_BUCKET_NAME
        self.file_name = file_name or GCS_STATE_FILE
        self._client = None

    def _get_client(self):
        """Get or create the GCS client."""
        if self._client is None:
            from google.cloud import storage

            self._client = storage.Client()
        return self._client

    def _get_blob(self):
        """Get the state file blob."""
        client = self._get_client()
        bucket = client.bucket(self.bucket_name)
        return bucket.blob(self.file_name)

    def load_notified_ids(self) -> set[str]:
        """Load notified IDs from Cloud Storage."""
        blob = self._get_blob()

        if not blob.exists():
            return set()

        try:
            content = blob.download_as_text()
            data = json.loads(content)
            return set(data.get("notified_competitions", []))
        except Exception as e:
            print(f"Warning: Failed to load from Cloud Storage: {e}")
            return set()

    def save_notified_ids(self, ids: set[str]) -> None:
        """Save notified IDs to Cloud Storage."""
        data = {
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "notified_competitions": sorted(ids),
        }

        blob = self._get_blob()
        blob.upload_from_string(
            json.dumps(data, indent=2, ensure_ascii=False),
            content_type="application/json",
        )


def get_storage() -> StorageBase:
    """Get the appropriate storage backend based on environment.

    Returns:
        LocalStorage for development, CloudStorage for production.
    """
    if ENV == "production" and GCS_BUCKET_NAME:
        return CloudStorage()
    return LocalStorage()


class CompetitionTracker:
    """Track and detect new competitions."""

    def __init__(self, storage: StorageBase | None = None):
        """Initialize the tracker.

        Args:
            storage: Storage backend to use. Defaults to auto-detect.
        """
        self.storage = storage or get_storage()
        self._notified_ids: set[str] | None = None

    @property
    def notified_ids(self) -> set[str]:
        """Get the set of notified competition IDs (lazy loaded)."""
        if self._notified_ids is None:
            self._notified_ids = self.storage.load_notified_ids()
        return self._notified_ids

    def find_new_competitions(
        self, competitions: list[Competition]
    ) -> list[Competition]:
        """Find competitions that haven't been notified yet.

        Args:
            competitions: List of competitions to check.

        Returns:
            List of new competitions that need notification.
        """
        return [comp for comp in competitions if comp.id not in self.notified_ids]

    def mark_as_notified(self, competition: Competition) -> None:
        """Mark a competition as notified.

        Args:
            competition: The competition to mark.
        """
        self.notified_ids.add(competition.id)

    def save(self) -> None:
        """Save the current state to storage."""
        if self._notified_ids is not None:
            self.storage.save_notified_ids(self._notified_ids)
