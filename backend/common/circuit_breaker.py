"""Shared pybreaker configuration; state transitions are owned by the library."""

import logging
from functools import lru_cache

from pybreaker import CircuitBreaker, CircuitBreakerListener

logger = logging.getLogger(__name__)


class CircuitLoggingListener(CircuitBreakerListener):
    def state_change(self, cb, old_state, new_state):
        level = logging.WARNING if new_state.name == "open" else logging.INFO
        logger.log(level, "Integration circuit %s: %s", new_state.name, cb.name)


@lru_cache(maxsize=32)
def get_circuit_breaker(name, failure_threshold, recovery_timeout, is_failure=None):
    """Reuse a configured pybreaker instance across clients in this process."""
    exclude = [lambda error: not is_failure(error)] if is_failure else []
    return CircuitBreaker(
        name=name,
        fail_max=failure_threshold,
        reset_timeout=recovery_timeout,
        exclude=exclude,
        listeners=[CircuitLoggingListener()],
        throw_new_error_on_trip=False,
    )
