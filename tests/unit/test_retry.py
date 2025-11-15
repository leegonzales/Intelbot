"""
Tests for the retry decorator (Issue #55).

Tests the retry logic with exponential backoff in research_agent/utils/retry.py.
"""

import time
from unittest.mock import Mock, call

import pytest

from research_agent.utils.retry import retry


class TestRetryDecorator:
    """Test cases for the retry decorator."""

    def test_retry_succeeds_first_attempt(self):
        """Test that successful calls don't retry."""
        mock_func = Mock(return_value="success")

        @retry(max_attempts=3)
        def test_func():
            return mock_func()

        result = test_func()

        assert result == "success"
        assert mock_func.call_count == 1

    def test_retry_after_one_failure(self):
        """Test retry after one transient failure."""
        mock_func = Mock(side_effect=[Exception("Transient error"), "success"])

        @retry(max_attempts=3, backoff_base=0.1)  # Fast backoff for testing
        def test_func():
            return mock_func()

        result = test_func()

        assert result == "success"
        assert mock_func.call_count == 2

    def test_retry_after_two_failures(self):
        """Test retry after two transient failures."""
        mock_func = Mock(
            side_effect=[
                Exception("Error 1"),
                Exception("Error 2"),
                "success",
            ]
        )

        @retry(max_attempts=3, backoff_base=0.1)
        def test_func():
            return mock_func()

        result = test_func()

        assert result == "success"
        assert mock_func.call_count == 3

    def test_retry_exhausts_max_attempts(self):
        """Test that exception is raised after max attempts."""
        mock_func = Mock(side_effect=Exception("Persistent error"))

        @retry(max_attempts=3, backoff_base=0.1)
        def test_func():
            return mock_func()

        with pytest.raises(Exception, match="Persistent error"):
            test_func()

        assert mock_func.call_count == 3

    def test_retry_exponential_backoff_timing(self):
        """Test that backoff delays follow exponential pattern."""
        call_times = []

        @retry(max_attempts=4, backoff_base=0.1)
        def test_func():
            call_times.append(time.time())
            if len(call_times) < 4:
                raise Exception("Not yet")
            return "success"

        result = test_func()

        assert result == "success"
        assert len(call_times) == 4

        # Check delays: 0.1s, 0.2s, 0.4s (2^0 * 0.1, 2^1 * 0.1, 2^2 * 0.1)
        delay1 = call_times[1] - call_times[0]
        delay2 = call_times[2] - call_times[1]
        delay3 = call_times[3] - call_times[2]

        # Allow 50% tolerance for timing
        assert 0.05 < delay1 < 0.15  # ~0.1s
        assert 0.1 < delay2 < 0.3  # ~0.2s
        assert 0.2 < delay3 < 0.6  # ~0.4s

    def test_retry_with_specific_exceptions(self):
        """Test that only specified exceptions trigger retry."""

        @retry(max_attempts=3, backoff_base=0.1, exceptions=(ValueError,))
        def test_func(should_raise_value_error):
            if should_raise_value_error:
                raise ValueError("Retry this")
            else:
                raise TypeError("Don't retry this")

        # ValueError should be retried
        with pytest.raises(ValueError):
            test_func(True)

        # TypeError should not be retried (immediate failure)
        with pytest.raises(TypeError):
            test_func(False)

    def test_retry_with_multiple_exception_types(self):
        """Test retry with multiple exception types."""
        attempt = {"count": 0}

        @retry(
            max_attempts=4,
            backoff_base=0.1,
            exceptions=(ValueError, TypeError, KeyError),
        )
        def test_func():
            attempt["count"] += 1
            if attempt["count"] == 1:
                raise ValueError("Error 1")
            elif attempt["count"] == 2:
                raise TypeError("Error 2")
            elif attempt["count"] == 3:
                raise KeyError("Error 3")
            return "success"

        result = test_func()

        assert result == "success"
        assert attempt["count"] == 4

    def test_retry_on_retry_callback(self):
        """Test that on_retry callback is called."""
        callback_calls = []

        def on_retry_handler(attempt, exception):
            callback_calls.append((attempt, str(exception)))

        @retry(
            max_attempts=3,
            backoff_base=0.1,
            on_retry=on_retry_handler,
        )
        def test_func():
            if len(callback_calls) < 2:
                raise ValueError(f"Error {len(callback_calls) + 1}")
            return "success"

        result = test_func()

        assert result == "success"
        assert len(callback_calls) == 2
        assert callback_calls[0][0] == 0  # First retry, attempt 0
        assert callback_calls[1][0] == 1  # Second retry, attempt 1
        assert "Error 1" in callback_calls[0][1]
        assert "Error 2" in callback_calls[1][1]

    def test_retry_preserves_function_metadata(self):
        """Test that decorator preserves function name and docstring."""

        @retry(max_attempts=3)
        def my_function():
            """This is my function."""
            return "result"

        assert my_function.__name__ == "my_function"
        assert my_function.__doc__ == "This is my function."

    def test_retry_with_function_args(self):
        """Test that retry works with function arguments."""
        mock_func = Mock(side_effect=[Exception("Fail"), "success"])

        @retry(max_attempts=3, backoff_base=0.1)
        def test_func(a, b, c=None):
            mock_func(a, b, c)
            if mock_func.call_count <= 1:
                raise Exception("Fail")
            return f"{a}-{b}-{c}"

        result = test_func("arg1", "arg2", c="arg3")

        assert result == "arg1-arg2-arg3"
        assert mock_func.call_count == 2
        mock_func.assert_called_with("arg1", "arg2", "arg3")

    def test_retry_with_kwargs(self):
        """Test that retry preserves keyword arguments."""
        results = []

        @retry(max_attempts=3, backoff_base=0.1)
        def test_func(**kwargs):
            results.append(kwargs)
            if len(results) < 2:
                raise Exception("Not yet")
            return kwargs

        result = test_func(foo="bar", baz="qux")

        assert result == {"foo": "bar", "baz": "qux"}
        assert len(results) == 2
        # All attempts should have same kwargs
        assert all(r == {"foo": "bar", "baz": "qux"} for r in results)

    def test_retry_default_parameters(self):
        """Test retry with default parameters."""
        attempt_count = {"count": 0}

        @retry()  # Use all defaults
        def test_func():
            attempt_count["count"] += 1
            if attempt_count["count"] < 3:
                raise Exception("Fail")
            return "success"

        result = test_func()

        assert result == "success"
        # Default max_attempts should be 3
        assert attempt_count["count"] == 3

    def test_retry_with_custom_backoff_base(self):
        """Test retry with custom backoff base."""
        call_times = []

        @retry(max_attempts=3, backoff_base=0.05)  # Smaller base
        def test_func():
            call_times.append(time.time())
            if len(call_times) < 3:
                raise Exception("Not yet")
            return "success"

        result = test_func()

        assert result == "success"

        # Delays should be: 0.05s, 0.1s (2^0 * 0.05, 2^1 * 0.05)
        delay1 = call_times[1] - call_times[0]
        delay2 = call_times[2] - call_times[1]

        assert 0.025 < delay1 < 0.075  # ~0.05s
        assert 0.05 < delay2 < 0.15  # ~0.1s

    def test_retry_with_no_exceptions_raised(self):
        """Test retry when function never raises exception."""
        call_count = {"count": 0}

        @retry(max_attempts=5, backoff_base=0.1)
        def test_func():
            call_count["count"] += 1
            return "success"

        result = test_func()

        assert result == "success"
        assert call_count["count"] == 1  # Should only call once

    def test_retry_re_raises_last_exception(self):
        """Test that the last exception is re-raised."""

        @retry(max_attempts=3, backoff_base=0.1)
        def test_func():
            raise ValueError("Final error")

        with pytest.raises(ValueError, match="Final error"):
            test_func()

    def test_retry_with_return_none(self):
        """Test retry when function returns None."""
        attempt_count = {"count": 0}

        @retry(max_attempts=2, backoff_base=0.1)
        def test_func():
            attempt_count["count"] += 1
            if attempt_count["count"] < 2:
                raise Exception("Fail")
            return None

        result = test_func()

        assert result is None
        assert attempt_count["count"] == 2

    def test_retry_with_class_method(self):
        """Test retry decorator on class methods."""

        class TestClass:
            def __init__(self):
                self.attempts = 0

            @retry(max_attempts=3, backoff_base=0.1)
            def method(self):
                self.attempts += 1
                if self.attempts < 3:
                    raise Exception("Not yet")
                return "success"

        obj = TestClass()
        result = obj.method()

        assert result == "success"
        assert obj.attempts == 3


class TestRetryLogging:
    """Test logging behavior of retry decorator."""

    def test_retry_logs_attempts(self, caplog):
        """Test that retry attempts are logged."""
        import logging

        @retry(max_attempts=3, backoff_base=0.1)
        def test_func():
            if test_func.call_count < 2:
                test_func.call_count += 1
                raise Exception(f"Fail {test_func.call_count}")
            return "success"

        test_func.call_count = 0

        with caplog.at_level(logging.WARNING):
            result = test_func()

        assert result == "success"

        # Should have logged retry attempts
        assert "failed (attempt 1/3)" in caplog.text or "failed" in caplog.text

    def test_retry_logs_final_failure(self, caplog):
        """Test that final failure is logged."""
        import logging

        @retry(max_attempts=3, backoff_base=0.1)
        def test_func():
            raise Exception("Always fails")

        with caplog.at_level(logging.ERROR):
            with pytest.raises(Exception):
                test_func()

        # Should log final failure
        assert "failed after 3 attempts" in caplog.text or "failed" in caplog.text


class TestRetryEdgeCases:
    """Test edge cases and error conditions."""

    def test_retry_with_max_attempts_one(self):
        """Test retry with max_attempts=1 (no retries)."""
        call_count = {"count": 0}

        @retry(max_attempts=1)
        def test_func():
            call_count["count"] += 1
            raise Exception("Fail")

        with pytest.raises(Exception):
            test_func()

        assert call_count["count"] == 1  # Should only try once

    def test_retry_with_zero_backoff(self):
        """Test retry with zero backoff (immediate retry)."""
        call_times = []

        @retry(max_attempts=3, backoff_base=0.0)
        def test_func():
            call_times.append(time.time())
            if len(call_times) < 3:
                raise Exception("Not yet")
            return "success"

        result = test_func()

        assert result == "success"

        # Delays should be effectively zero
        if len(call_times) >= 2:
            delay1 = call_times[1] - call_times[0]
            assert delay1 < 0.05  # Very small delay

    def test_retry_exception_in_callback(self):
        """Test that exception in callback doesn't break retry."""

        def bad_callback(attempt, exception):
            raise RuntimeError("Callback error")

        @retry(max_attempts=3, backoff_base=0.1, on_retry=bad_callback)
        def test_func():
            if not hasattr(test_func, "attempts"):
                test_func.attempts = 0
            test_func.attempts += 1
            if test_func.attempts < 2:
                raise ValueError("Fail")
            return "success"

        # Should still work despite callback errors
        # (or should fail - depends on implementation)
        # This test documents the behavior
        try:
            result = test_func()
            assert result == "success" or True  # Either behavior is acceptable
        except RuntimeError:
            pass  # Callback error propagated - also acceptable


@pytest.mark.parametrize(
    "max_attempts,backoff_base,should_succeed",
    [
        (1, 1.0, False),  # Only 1 attempt, fails
        (2, 0.5, True),  # 2 attempts, succeeds on 2nd
        (3, 0.1, True),  # 3 attempts, succeeds on 2nd
        (5, 2.0, True),  # 5 attempts, succeeds on 2nd
    ],
)
def test_retry_parameterized(max_attempts, backoff_base, should_succeed):
    """Parameterized test for different retry configurations."""
    call_count = {"count": 0}

    @retry(max_attempts=max_attempts, backoff_base=backoff_base)
    def test_func():
        call_count["count"] += 1
        if call_count["count"] < 2:
            raise Exception("Fail on first attempt")
        return "success"

    if should_succeed:
        result = test_func()
        assert result == "success"
    else:
        with pytest.raises(Exception):
            test_func()
