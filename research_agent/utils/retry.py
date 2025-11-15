"""Retry decorator with exponential backoff."""

import time
import functools
from typing import Callable, Tuple, Type
from research_agent.utils.logger import get_logger

logger = get_logger("retry")


def retry(
    max_attempts: int = 3,
    backoff_base: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Callable = None
):
    """
    Decorator to retry a function with exponential backoff.

    Args:
        max_attempts: Maximum number of attempts (default: 3)
        backoff_base: Base delay in seconds (default: 2.0)
                     Delay = backoff_base * (2 ** attempt)
                     e.g., 2s, 4s, 8s for attempts 0, 1, 2
        exceptions: Tuple of exception types to catch and retry
        on_retry: Optional callback function called on each retry
                  Signature: on_retry(attempt, exception, delay)

    Returns:
        Decorated function

    Example:
        @retry(max_attempts=3, backoff_base=2.0, exceptions=(RequestException,))
        def fetch_data():
            return requests.get("https://api.example.com")
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)

                except exceptions as e:
                    last_exception = e

                    # If this was the last attempt, raise the exception
                    if attempt == max_attempts - 1:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise

                    # Calculate delay with exponential backoff
                    delay = backoff_base * (2 ** attempt)

                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt + 1}/{max_attempts}): {e}. "
                        f"Retrying in {delay}s..."
                    )

                    # Call custom retry callback if provided
                    if on_retry:
                        on_retry(attempt, e, delay)

                    # Wait before retrying
                    time.sleep(delay)

            # This should never be reached, but just in case
            if last_exception:
                raise last_exception

        return wrapper
    return decorator


def retry_with_config(config_dict: dict):
    """
    Create retry decorator from config dictionary.

    Args:
        config_dict: Dict with keys 'max_attempts', 'backoff_base', etc.

    Returns:
        retry decorator configured from dict

    Example:
        config = {'max_attempts': 3, 'backoff_base': 2.0}
        @retry_with_config(config)
        def my_function():
            pass
    """
    return retry(
        max_attempts=config_dict.get('max_attempts', 3),
        backoff_base=config_dict.get('backoff_base', 2.0),
        exceptions=tuple(config_dict.get('exceptions', [Exception]))
    )
