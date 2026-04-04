"""Tests for CloudStorage class."""

import json
from unittest.mock import MagicMock, patch

from src.competition_tracker import CloudStorage


class TestCloudStorage:
    """Tests for CloudStorage class."""

    def _make_storage(self):
        """Create a CloudStorage with mocked GCS client."""
        storage = CloudStorage(bucket_name="test-bucket", file_name="state.json")
        storage._client = MagicMock()
        return storage

    def _mock_blob(self, storage, exists=True, content=None):
        """Set up a mock blob on the storage's client."""
        blob = MagicMock()
        blob.exists.return_value = exists
        if content is not None:
            blob.download_as_text.return_value = json.dumps(content)
        storage._client.bucket.return_value.blob.return_value = blob
        return blob

    def test_load_notified_ids_blob_not_exists(self):
        """Should return empty set when blob doesn't exist."""
        storage = self._make_storage()
        self._mock_blob(storage, exists=False)

        result = storage.load_notified_ids()

        assert result == set()

    def test_load_notified_ids_success(self):
        """Should load IDs from Cloud Storage."""
        storage = self._make_storage()
        content = {
            "last_updated": "2025-01-01T00:00:00Z",
            "notified_competitions": ["comp1", "comp2"],
        }
        self._mock_blob(storage, exists=True, content=content)

        result = storage.load_notified_ids()

        assert result == {"comp1", "comp2"}

    def test_load_notified_ids_error_returns_empty(self):
        """Should return empty set on download error."""
        storage = self._make_storage()
        blob = self._mock_blob(storage, exists=True)
        blob.download_as_text.side_effect = Exception("Network error")

        result = storage.load_notified_ids()

        assert result == set()

    def test_save_notified_ids(self):
        """Should upload JSON to Cloud Storage."""
        storage = self._make_storage()
        blob = self._mock_blob(storage)

        storage.save_notified_ids({"comp1", "comp2"})

        blob.upload_from_string.assert_called_once()
        args = blob.upload_from_string.call_args
        data = json.loads(args[0][0])
        assert set(data["notified_competitions"]) == {"comp1", "comp2"}
        assert "last_updated" in data
        assert args[1]["content_type"] == "application/json"

    def test_bucket_and_file_name(self):
        """Should use provided bucket and file names."""
        storage = CloudStorage(bucket_name="my-bucket", file_name="my-state.json")
        assert storage.bucket_name == "my-bucket"
        assert storage.file_name == "my-state.json"

    def test_default_config_values(self):
        """Should fall back to config defaults when not provided."""
        with patch("src.competition_tracker.GCS_BUCKET_NAME", "default-bucket"), \
             patch("src.competition_tracker.GCS_STATE_FILE", "default.json"):
            storage = CloudStorage()
            assert storage.bucket_name == "default-bucket"
            assert storage.file_name == "default.json"

    def test_get_client_lazy_init(self):
        """Should lazily initialize GCS client and cache it."""
        storage = CloudStorage(bucket_name="test-bucket")
        assert storage._client is None

        mock_client = MagicMock()
        storage._client = mock_client

        # Once set, _get_client should return the cached client
        assert storage._get_client() is mock_client
