"""
Tests for the logging system (Issue #54).

Tests the centralized logging configuration in research_agent/utils/logger.py.
"""

import logging
import os
from datetime import datetime
from pathlib import Path

import pytest

from research_agent.utils.logger import get_logger, setup_logger


class TestSetupLogger:
    """Test cases for setup_logger function."""

    def test_setup_logger_creates_logger(self, temp_dir):
        """Test that setup_logger creates a logger instance."""
        logger = setup_logger(
            name="test_logger",
            log_dir=temp_dir,
            verbose=False,
            log_to_file=True,
        )

        assert logger is not None
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"

    def test_setup_logger_sets_info_level_by_default(self, temp_dir):
        """Test that default log level is INFO when verbose=False."""
        logger = setup_logger(
            name="test_info",
            log_dir=temp_dir,
            verbose=False,
        )

        assert logger.level == logging.INFO

    def test_setup_logger_sets_debug_level_when_verbose(self, temp_dir):
        """Test that log level is DEBUG when verbose=True."""
        logger = setup_logger(
            name="test_debug",
            log_dir=temp_dir,
            verbose=True,
        )

        assert logger.level == logging.DEBUG

    def test_setup_logger_creates_file_handler(self, temp_dir):
        """Test that file handler is created when log_to_file=True."""
        logger = setup_logger(
            name="test_file_handler",
            log_dir=temp_dir,
            log_to_file=True,
        )

        # Should have at least 2 handlers: file + console
        assert len(logger.handlers) >= 2

        # Check that one handler is a RotatingFileHandler
        from logging.handlers import RotatingFileHandler

        has_file_handler = any(
            isinstance(h, RotatingFileHandler) for h in logger.handlers
        )
        assert has_file_handler

    def test_setup_logger_creates_console_handler(self, temp_dir):
        """Test that console handler is always created."""
        logger = setup_logger(
            name="test_console_handler",
            log_dir=temp_dir,
        )

        # Check that one handler is a StreamHandler
        has_console_handler = any(
            isinstance(h, logging.StreamHandler) and not hasattr(h, "baseFilename")
            for h in logger.handlers
        )
        assert has_console_handler

    def test_setup_logger_without_file_logging(self, temp_dir):
        """Test that no file handler is created when log_to_file=False."""
        logger = setup_logger(
            name="test_no_file",
            log_dir=temp_dir,
            log_to_file=False,
        )

        from logging.handlers import RotatingFileHandler

        has_file_handler = any(
            isinstance(h, RotatingFileHandler) for h in logger.handlers
        )
        assert not has_file_handler

        # Should still have console handler
        assert len(logger.handlers) >= 1

    def test_setup_logger_creates_log_directory(self, temp_dir):
        """Test that log directory is created if it doesn't exist."""
        log_dir = temp_dir / "new_logs"
        assert not log_dir.exists()

        setup_logger(
            name="test_mkdir",
            log_dir=log_dir,
            log_to_file=True,
        )

        assert log_dir.exists()
        assert log_dir.is_dir()

    def test_setup_logger_creates_dated_log_file(self, temp_dir):
        """Test that log file name includes current date."""
        logger = setup_logger(
            name="test_dated_file",
            log_dir=temp_dir,
            log_to_file=True,
        )

        # Get the file handler
        from logging.handlers import RotatingFileHandler

        file_handler = next(
            h for h in logger.handlers if isinstance(h, RotatingFileHandler)
        )

        # Check filename includes date
        log_filename = Path(file_handler.baseFilename).name
        expected_date = datetime.now().strftime("%Y-%m-%d")
        assert expected_date in log_filename

    def test_setup_logger_prevents_duplicate_handlers(self, temp_dir):
        """Test that calling setup_logger twice doesn't duplicate handlers."""
        logger1 = setup_logger(
            name="test_duplicate",
            log_dir=temp_dir,
        )
        handler_count_1 = len(logger1.handlers)

        # Call setup again with same name
        logger2 = setup_logger(
            name="test_duplicate",
            log_dir=temp_dir,
        )

        # Should return same logger
        assert logger1 is logger2

        # Should have same number of handlers (not duplicated)
        assert len(logger2.handlers) == handler_count_1

    def test_setup_logger_file_rotation_settings(self, temp_dir):
        """Test that file handler has correct rotation settings."""
        logger = setup_logger(
            name="test_rotation",
            log_dir=temp_dir,
            log_to_file=True,
        )

        from logging.handlers import RotatingFileHandler

        file_handler = next(
            h for h in logger.handlers if isinstance(h, RotatingFileHandler)
        )

        # Check rotation settings
        assert file_handler.maxBytes == 10 * 1024 * 1024  # 10MB
        assert file_handler.backupCount == 30  # 30 backups

    def test_setup_logger_file_formatter(self, temp_dir):
        """Test that file handler has detailed formatter."""
        logger = setup_logger(
            name="test_file_format",
            log_dir=temp_dir,
            log_to_file=True,
        )

        from logging.handlers import RotatingFileHandler

        file_handler = next(
            h for h in logger.handlers if isinstance(h, RotatingFileHandler)
        )

        formatter = file_handler.formatter
        assert formatter is not None

        # Check formatter includes expected fields
        format_str = formatter._fmt
        assert "%(asctime)s" in format_str
        assert "%(name)s" in format_str
        assert "%(levelname)s" in format_str
        assert "%(message)s" in format_str

    def test_setup_logger_console_formatter(self, temp_dir):
        """Test that console handler has simple formatter."""
        logger = setup_logger(
            name="test_console_format",
            log_dir=temp_dir,
        )

        console_handler = next(
            h
            for h in logger.handlers
            if isinstance(h, logging.StreamHandler)
            and not hasattr(h, "baseFilename")
        )

        formatter = console_handler.formatter
        assert formatter is not None

        # Console formatter should be simpler
        format_str = formatter._fmt
        assert "%(levelname)s" in format_str
        assert "%(message)s" in format_str

    def test_setup_logger_console_handler_verbose_level(self, temp_dir):
        """Test that console handler respects verbose flag for level."""
        # Non-verbose
        logger1 = setup_logger(
            name="test_console_level_1",
            log_dir=temp_dir,
            verbose=False,
        )

        console_handler_1 = next(
            h
            for h in logger1.handlers
            if isinstance(h, logging.StreamHandler)
            and not hasattr(h, "baseFilename")
        )
        assert console_handler_1.level == logging.INFO

        # Verbose
        logger2 = setup_logger(
            name="test_console_level_2",
            log_dir=temp_dir,
            verbose=True,
        )

        console_handler_2 = next(
            h
            for h in logger2.handlers
            if isinstance(h, logging.StreamHandler)
            and not hasattr(h, "baseFilename")
        )
        assert console_handler_2.level == logging.DEBUG

    def test_setup_logger_actually_logs_to_file(self, temp_dir):
        """Test that logger actually writes to file."""
        logger = setup_logger(
            name="test_actual_logging",
            log_dir=temp_dir,
            log_to_file=True,
        )

        test_message = "Test log message for file writing"
        logger.info(test_message)

        # Find the log file
        log_files = list(temp_dir.glob("*.log"))
        assert len(log_files) > 0

        # Read log file and verify message
        log_content = log_files[0].read_text()
        assert test_message in log_content


class TestGetLogger:
    """Test cases for get_logger function."""

    def test_get_logger_creates_child_logger(self):
        """Test that get_logger creates a child logger."""
        logger = get_logger("test.component")

        assert logger is not None
        assert isinstance(logger, logging.Logger)
        assert logger.name == "research_agent.test.component"

    def test_get_logger_with_simple_name(self):
        """Test get_logger with simple component name."""
        logger = get_logger("simple")

        assert logger.name == "research_agent.simple"

    def test_get_logger_with_nested_name(self):
        """Test get_logger with nested component name."""
        logger = get_logger("agents.source")

        assert logger.name == "research_agent.agents.source"

    def test_get_logger_returns_same_instance(self):
        """Test that get_logger returns same instance for same name."""
        logger1 = get_logger("same_component")
        logger2 = get_logger("same_component")

        assert logger1 is logger2

    def test_get_logger_inherits_parent_config(self, temp_dir):
        """Test that child logger inherits parent configuration."""
        # Set up parent logger
        parent = setup_logger(
            name="research_agent",
            log_dir=temp_dir,
            verbose=True,
        )

        # Get child logger
        child = get_logger("test_child")

        # Child should inherit parent's effective level
        # (Note: child.level will be NOTSET, but effectiveLevel checks parent)
        assert child.getEffectiveLevel() == logging.DEBUG


class TestLoggingIntegration:
    """Integration tests for logging system."""

    def test_logging_all_levels(self, temp_dir, caplog):
        """Test that all log levels work correctly."""
        logger = setup_logger(
            name="test_all_levels",
            log_dir=temp_dir,
            verbose=True,
            log_to_file=False,  # Easier to test with caplog
        )

        with caplog.at_level(logging.DEBUG):
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")

        # Check all messages were logged
        assert "Debug message" in caplog.text
        assert "Info message" in caplog.text
        assert "Warning message" in caplog.text
        assert "Error message" in caplog.text

    def test_logging_respects_level(self, temp_dir, caplog):
        """Test that log level filtering works."""
        logger = setup_logger(
            name="test_level_filter",
            log_dir=temp_dir,
            verbose=False,  # INFO level
            log_to_file=False,
        )

        with caplog.at_level(logging.DEBUG):
            logger.debug("Should not appear")
            logger.info("Should appear")
            logger.warning("Should appear")

        # Debug should be filtered out
        assert "Should not appear" not in caplog.text
        assert "Should appear" in caplog.text

    def test_logging_with_exception_info(self, temp_dir):
        """Test logging with exception traceback."""
        logger = setup_logger(
            name="test_exception",
            log_dir=temp_dir,
            log_to_file=True,
        )

        try:
            raise ValueError("Test exception")
        except ValueError:
            logger.error("Error occurred", exc_info=True)

        # Check that traceback was written to log file
        log_files = list(temp_dir.glob("*.log"))
        log_content = log_files[0].read_text()

        assert "Error occurred" in log_content
        assert "ValueError: Test exception" in log_content
        assert "Traceback" in log_content

    def test_multiple_loggers_same_file(self, temp_dir):
        """Test that multiple loggers can write to same log dir."""
        logger1 = setup_logger("test_multi_1", log_dir=temp_dir)
        logger2 = setup_logger("test_multi_2", log_dir=temp_dir)

        logger1.info("Message from logger 1")
        logger2.info("Message from logger 2")

        # Both should write to files dated today
        log_files = list(temp_dir.glob("*.log"))
        assert len(log_files) == 2  # One per logger

    def test_logger_thread_safety(self, temp_dir):
        """Test that logger is thread-safe."""
        import threading

        logger = setup_logger("test_threads", log_dir=temp_dir)

        def log_messages(thread_id):
            for i in range(10):
                logger.info(f"Thread {thread_id} message {i}")

        threads = [threading.Thread(target=log_messages, args=(i,)) for i in range(5)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # All messages should be in log file
        log_files = list(temp_dir.glob("*.log"))
        log_content = log_files[0].read_text()

        # Should have 50 messages total (5 threads * 10 messages)
        message_count = log_content.count("Thread")
        assert message_count == 50


@pytest.mark.parametrize(
    "verbose,expected_level",
    [
        (True, logging.DEBUG),
        (False, logging.INFO),
    ],
)
def test_logger_verbose_parameterized(temp_dir, verbose, expected_level):
    """Parameterized test for verbose flag."""
    logger = setup_logger(
        name=f"test_param_{verbose}",
        log_dir=temp_dir,
        verbose=verbose,
    )

    assert logger.level == expected_level
