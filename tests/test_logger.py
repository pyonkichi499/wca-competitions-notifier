"""Tests for logger module."""

import json
import logging

import pytest

from src.logger import (
    CloudRunJsonFormatter,
    LocalFormatter,
    create_formatter,
    is_cloud_run,
    setup_logging,
)


class TestIsCloudRun:
    """Tests for is_cloud_run function."""

    def test_returns_false_locally(self, monkeypatch):
        """Should return False when K_SERVICE is not set."""
        monkeypatch.delenv("K_SERVICE", raising=False)
        assert is_cloud_run() is False

    def test_returns_true_in_cloud_run(self, monkeypatch):
        """Should return True when K_SERVICE is set."""
        monkeypatch.setenv("K_SERVICE", "my-service")
        assert is_cloud_run() is True


class TestCloudRunJsonFormatter:
    """Tests for CloudRunJsonFormatter class."""

    def test_format_basic_message(self):
        """Should format log as JSON with required fields."""
        formatter = CloudRunJsonFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/app/test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        parsed = json.loads(result)

        assert parsed["severity"] == "INFO"
        assert parsed["message"] == "Test message"
        assert parsed["logger"] == "test.logger"
        assert "timestamp" in parsed
        assert parsed["logging.googleapis.com/sourceLocation"]["file"] == "/app/test.py"
        assert parsed["logging.googleapis.com/sourceLocation"]["line"] == 42

    def test_format_with_args(self):
        """Should format message with arguments."""
        formatter = CloudRunJsonFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Found %d items",
            args=(5,),
            exc_info=None,
        )

        result = formatter.format(record)
        parsed = json.loads(result)

        assert parsed["message"] == "Found 5 items"

    def test_severity_mapping(self):
        """Should map Python log levels to Cloud Logging severity."""
        formatter = CloudRunJsonFormatter()

        test_cases = [
            (logging.DEBUG, "DEBUG"),
            (logging.INFO, "INFO"),
            (logging.WARNING, "WARNING"),
            (logging.ERROR, "ERROR"),
            (logging.CRITICAL, "CRITICAL"),
        ]

        for level, expected_severity in test_cases:
            record = logging.LogRecord(
                name="test",
                level=level,
                pathname="test.py",
                lineno=1,
                msg="Test",
                args=(),
                exc_info=None,
            )
            result = formatter.format(record)
            parsed = json.loads(result)
            assert parsed["severity"] == expected_severity

    def test_format_with_exception(self):
        """Should include exception info when present."""
        formatter = CloudRunJsonFormatter()

        try:
            raise ValueError("Test error")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )

        result = formatter.format(record)
        parsed = json.loads(result)

        assert "exception" in parsed
        assert "ValueError" in parsed["exception"]
        assert "Test error" in parsed["exception"]


class TestLocalFormatter:
    """Tests for LocalFormatter class."""

    def test_format_includes_timestamp(self):
        """Should include timestamp in output."""
        formatter = LocalFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)

        assert "INFO" in result
        assert "test.logger" in result
        assert "Test message" in result


class TestCreateFormatter:
    """Tests for create_formatter function."""

    def test_json_format_type(self):
        """Should return JSON formatter when format_type is 'json'."""
        formatter = create_formatter(format_type="json")
        assert isinstance(formatter, CloudRunJsonFormatter)

    def test_text_format_type(self):
        """Should return local formatter when format_type is 'text'."""
        formatter = create_formatter(format_type="text")
        assert isinstance(formatter, LocalFormatter)

    def test_auto_with_cloud_run_true(self):
        """Should return JSON formatter when auto and Cloud Run detected."""
        formatter = create_formatter(
            format_type="auto",
            cloud_run_detector=lambda: True,
        )
        assert isinstance(formatter, CloudRunJsonFormatter)

    def test_auto_with_cloud_run_false(self):
        """Should return local formatter when auto and not Cloud Run."""
        formatter = create_formatter(
            format_type="auto",
            cloud_run_detector=lambda: False,
        )
        assert isinstance(formatter, LocalFormatter)


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_setup_with_text_format(self):
        """Should configure text formatter."""
        setup_logging(level="INFO", format_type="text")

        logger = logging.getLogger()
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0].formatter, LocalFormatter)

    def test_setup_with_json_format(self):
        """Should configure JSON formatter."""
        setup_logging(level="INFO", format_type="json")

        logger = logging.getLogger()
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0].formatter, CloudRunJsonFormatter)

    def test_setup_with_di_detector(self):
        """Should use injected cloud_run_detector."""
        # Simulate Cloud Run environment via DI
        setup_logging(
            level="INFO",
            format_type="auto",
            cloud_run_detector=lambda: True,
        )

        logger = logging.getLogger()
        assert isinstance(logger.handlers[0].formatter, CloudRunJsonFormatter)

    def test_clears_existing_handlers(self):
        """Should clear existing handlers before adding new one."""
        logger = logging.getLogger()

        # Add some handlers manually
        logger.addHandler(logging.StreamHandler())
        logger.addHandler(logging.StreamHandler())
        assert len(logger.handlers) >= 2

        # Setup should clear them
        setup_logging(level="INFO", format_type="text")

        assert len(logger.handlers) == 1
