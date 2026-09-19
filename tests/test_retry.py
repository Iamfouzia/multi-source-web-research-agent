import pytest

from research_agent.retry import call_with_retries


def test_call_with_retries_succeeds_after_failures():
    calls = {"count": 0}

    def flaky():
        calls["count"] += 1
        if calls["count"] < 3:
            raise ValueError("temporary failure")
        return "ok"

    result = call_with_retries(flaky, max_retries=3, backoff_seconds=0)

    assert result == "ok"
    assert calls["count"] == 3


def test_call_with_retries_raises_after_exhausting_attempts():
    def always_fails():
        raise ValueError("permanent failure")

    with pytest.raises(ValueError):
        call_with_retries(always_fails, max_retries=2, backoff_seconds=0)
