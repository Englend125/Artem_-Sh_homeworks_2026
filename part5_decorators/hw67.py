import json
from datetime import UTC, datetime, timedelta
from functools import wraps
from typing import Any, ParamSpec, Protocol, TypeVar
from urllib.request import urlopen

INVALID_CRITICAL_COUNT = "Breaker count must be positive integer!"
INVALID_RECOVERY_TIME = "Breaker recovery time must be positive integer!"
VALIDATIONS_FAILED = "Invalid decorator args."
TOO_MUCH = "Too much requests, just wait."

# comment
P = ParamSpec("P")
R_co = TypeVar("R_co", covariant=True)


class CallableWithMeta(Protocol[P, R_co]):
    __name__: str
    __module__: str

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R_co: ...


class BreakerError(Exception):
    def __init__(self, func_name: str, block_time: datetime):
        super().__init__(TOO_MUCH)
        self.func_name = func_name
        self.block_time = block_time


class CircuitBreaker:
    def __init__(
        self,
        critical_count: int,
        time_to_recover: int,
        triggers_on: type[Exception],
    ):
        errors = []
        if critical_count <= 0:
            errors.append(ValueError(INVALID_CRITICAL_COUNT))
        if time_to_recover <= 0:
            errors.append(ValueError(INVALID_RECOVERY_TIME))
        if errors:
            raise ExceptionGroup(VALIDATIONS_FAILED, errors)
        self.critical_count = critical_count
        self.time_to_recover = time_to_recover
        self.triggers_on = triggers_on

        self.fail_cnt = 0
        self.blocked_until: datetime | None = None

    def __call__(self, func: CallableWithMeta[P, R_co]) -> CallableWithMeta[P, R_co]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R_co:
            self._check(func)
            try:
                result = func(*args, **kwargs)
            except self.triggers_on as err:
                self._handle_error(func, err)
                raise
            except Exception:
                raise
            else:
                self.fail_cnt = 0
                return result

        return wrapper

    def _get_func_name(self, func: CallableWithMeta[P, R_co]) -> str:
        return f"{func.__module__}.{func.__name__}"

    def _check(self, func: CallableWithMeta[P, R_co]) -> None:
        now = datetime.now(UTC)

        if self.blocked_until is not None:
            if now < self.blocked_until:
                raise BreakerError(self._get_func_name(func), self.blocked_until)
            self.blocked_until = None
            self.fail_cnt = 0

    def _handle_error(self, func: CallableWithMeta[P, R_co], err: Exception) -> None:
        self.fail_cnt += 1
        if self.fail_cnt >= self.critical_count:
            block_time = datetime.now(UTC)
            self.blocked_until = block_time + timedelta(seconds=self.time_to_recover)
            raise BreakerError(self._get_func_name(func), block_time) from err


circuit_breaker = CircuitBreaker(5, 30, Exception)


# @circuit_breaker
def get_comments(post_id: int) -> Any:
    """
    Получает комментарии к посту

    Args:
        post_id (int): Идентификатор поста

    Returns:
        list[dict[int | str]]: Список комментариев
    """
    response = urlopen(f"https://jsonplaceholder.typicode.com/comments?postId={post_id}")
    return json.loads(response.read())


if __name__ == "__main__":
    comments = get_comments(1)
