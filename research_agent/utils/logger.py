"""Centralized logging configuration for Research Agent."""

import logging
import sys
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler


def setup_logger(
    name: str = "research_agent",
    log_dir: Path = None,
    verbose: bool = False,
    log_to_file: bool = True
) -> logging.Logger:
    """
    Set up logger with file and console handlers.

    Args:
        name: Logger name
        log_dir: Directory for log files
        verbose: If True, set DEBUG level; otherwise INFO
        log_to_file: If True, write logs to file

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Don't add handlers if already configured
    if logger.handlers:
        return logger

    # Set logger level
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    simple_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    console_handler.setFormatter(simple_formatter if not verbose else detailed_formatter)
    logger.addHandler(console_handler)

    # File handler (if enabled)
    if log_to_file and log_dir:
        log_dir = Path(log_dir).expanduser()
        log_dir.mkdir(parents=True, exist_ok=True)

        # Daily log file
        log_file = log_dir / f"{datetime.now():%Y-%m-%d}.log"

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=30  # Keep 30 days of logs
        )
        file_handler.setLevel(logging.DEBUG)  # Always log DEBUG to file
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    Get logger instance.

    Args:
        name: Logger name (default: research_agent)

    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f"research_agent.{name}")
    return logging.getLogger("research_agent")
