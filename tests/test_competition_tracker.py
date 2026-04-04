"""Tests for competition_tracker module."""

import json

from src.competition_tracker import (
    CompetitionTracker,
    LocalStorage,
)


class TestLocalStorage:
    """Tests for LocalStorage class."""

    def test_load_notified_ids_file_not_exists(self, tmp_path):
        """Should return empty set when file doesn't exist."""
        storage = LocalStorage(str(tmp_path / "nonexistent.json"))
        result = storage.load_notified_ids()
        assert result == set()

    def test_load_notified_ids_success(self, tmp_path):
        """Should load IDs from existing file."""
        state_file = tmp_path / "state.json"
        state_file.write_text(
            json.dumps(
                {
                    "last_updated": "2025-01-01T00:00:00Z",
                    "notified_competitions": ["comp1", "comp2"],
                }
            )
        )

        storage = LocalStorage(str(state_file))
        result = storage.load_notified_ids()

        assert result == {"comp1", "comp2"}

    def test_load_notified_ids_malformed_json(self, tmp_path):
        """Should return empty set for malformed JSON."""
        state_file = tmp_path / "state.json"
        state_file.write_text("not valid json")

        storage = LocalStorage(str(state_file))
        result = storage.load_notified_ids()

        assert result == set()

    def test_save_notified_ids(self, tmp_path):
        """Should save IDs to file."""
        state_file = tmp_path / "state.json"
        storage = LocalStorage(str(state_file))

        storage.save_notified_ids({"comp1", "comp2", "comp3"})

        assert state_file.exists()
        data = json.loads(state_file.read_text())
        assert set(data["notified_competitions"]) == {"comp1", "comp2", "comp3"}
        assert "last_updated" in data

    def test_save_creates_parent_directory(self, tmp_path):
        """Should create parent directory if it doesn't exist."""
        state_file = tmp_path / "subdir" / "state.json"
        storage = LocalStorage(str(state_file))

        storage.save_notified_ids({"comp1"})

        assert state_file.exists()


class TestCompetitionTracker:
    """Tests for CompetitionTracker class."""

    def test_find_new_competitions_all_new(
        self,
        tmp_path,
        sample_competition,
        sample_competition_yokohama,
    ):
        """Should find all competitions as new when none notified."""
        storage = LocalStorage(str(tmp_path / "state.json"))
        tracker = CompetitionTracker(storage=storage)

        competitions = [sample_competition, sample_competition_yokohama]
        result = tracker.find_new_competitions(competitions)

        assert len(result) == 2
        assert sample_competition in result
        assert sample_competition_yokohama in result

    def test_find_new_competitions_some_notified(
        self,
        tmp_path,
        sample_competition,
        sample_competition_yokohama,
    ):
        """Should exclude already notified competitions."""
        state_file = tmp_path / "state.json"
        state_file.write_text(
            json.dumps(
                {
                    "last_updated": "2025-01-01T00:00:00Z",
                    "notified_competitions": [sample_competition.id],
                }
            )
        )

        storage = LocalStorage(str(state_file))
        tracker = CompetitionTracker(storage=storage)

        competitions = [sample_competition, sample_competition_yokohama]
        result = tracker.find_new_competitions(competitions)

        assert len(result) == 1
        assert sample_competition_yokohama in result
        assert sample_competition not in result

    def test_find_new_competitions_all_notified(
        self,
        tmp_path,
        sample_competition,
    ):
        """Should return empty list when all competitions already notified."""
        state_file = tmp_path / "state.json"
        state_file.write_text(
            json.dumps(
                {
                    "last_updated": "2025-01-01T00:00:00Z",
                    "notified_competitions": [sample_competition.id],
                }
            )
        )

        storage = LocalStorage(str(state_file))
        tracker = CompetitionTracker(storage=storage)

        result = tracker.find_new_competitions([sample_competition])

        assert result == []

    def test_mark_as_notified(self, tmp_path, sample_competition):
        """Should add competition ID to notified set."""
        storage = LocalStorage(str(tmp_path / "state.json"))
        tracker = CompetitionTracker(storage=storage)

        assert sample_competition.id not in tracker.notified_ids

        tracker.mark_as_notified(sample_competition)

        assert sample_competition.id in tracker.notified_ids

    def test_save(self, tmp_path, sample_competition):
        """Should persist notified IDs to storage."""
        state_file = tmp_path / "state.json"
        storage = LocalStorage(str(state_file))
        tracker = CompetitionTracker(storage=storage)

        tracker.mark_as_notified(sample_competition)
        tracker.save()

        # Verify by loading again
        data = json.loads(state_file.read_text())
        assert sample_competition.id in data["notified_competitions"]

    def test_lazy_loading(self, tmp_path, sample_competition):
        """Should lazy load notified IDs."""
        state_file = tmp_path / "state.json"
        state_file.write_text(
            json.dumps(
                {
                    "last_updated": "2025-01-01T00:00:00Z",
                    "notified_competitions": ["existing_comp"],
                }
            )
        )

        storage = LocalStorage(str(state_file))
        tracker = CompetitionTracker(storage=storage)

        # _notified_ids should be None before first access
        assert tracker._notified_ids is None

        # Access triggers loading
        _ = tracker.notified_ids

        assert tracker._notified_ids is not None
        assert "existing_comp" in tracker.notified_ids
