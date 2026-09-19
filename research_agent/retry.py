import time
from typing import Callable, TypeVar

T = TypeVar("T")


def call_with_retries(
    func: Callable[[], T],
    max_retries: int,
    backoff_seconds: float = 1.5,
    retry_on: tuple[type[Exception], ...] = (Exception,),
) -> T:
    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            return func()
        except retry_on as exc:
            last_error = exc
            if attempt < max_retries:
                time.sleep(backoff_seconds * (attempt + 1))
    raise last_error  
