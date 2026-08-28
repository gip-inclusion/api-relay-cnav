import collections
import datetime
import multiprocessing.pool
import random
import time

import pytest
from django.core.management import call_command
from django.db import connection, transaction
from django.utils import timezone

from api_relay_cnav.rate_limit.limiter import (
    Limiter,
)
from api_relay_cnav.rate_limit.models import RateLimitCounter


def test_parse_date():
    limiter = Limiter("test", "10/sec")
    assert limiter.window_limit == 10
    assert limiter.window_seconds == 1
    assert limiter.bucket_seconds == 1

    limiter = Limiter("test", "234/min")
    assert limiter.window_limit == 234
    assert limiter.window_seconds == 60
    assert limiter.bucket_seconds == 2

    limiter = Limiter("test", "5_000/hour")
    assert limiter.window_limit == 5_000
    assert limiter.window_seconds == 3600
    assert limiter.bucket_seconds == 120

    limiter = Limiter("test", "2000/day")
    assert limiter.window_limit == 2_000
    assert limiter.window_seconds == 24 * 3600
    assert limiter.bucket_seconds == 3600


class TestRateLimitWaitingTime:
    def test_limit(self):
        limit = random.randint(10, 15)
        limiter = Limiter("test", rate=f"{limit}/min")
        for _i in range(limit):
            assert limiter.rate_limit_waiting_time("test_key") == 0
        assert limiter.rate_limit_waiting_time("test_key") in (
            limiter.window_seconds,
            limiter.window_seconds - limiter.bucket_seconds,  # If test runs accross 2 buckets
        )

        assert limiter.rate_limit_waiting_time("other_key") == 0
        assert limiter.rate_limit_waiting_time("test_key") in (
            limiter.window_seconds,
            limiter.window_seconds - limiter.bucket_seconds,
        )

    def set_history(self, limiter, client_key, history):
        with connection.cursor() as cursor:
            cursor.execute("SELECT (extract(epoch FROM now())::bigint / %s)", (limiter.bucket_seconds,))
            bucket_key = cursor.fetchone()[0]
        for i, value in enumerate(history):
            if value:
                RateLimitCounter.objects.create(
                    limiter_key=limiter.key,
                    client_key=client_key,
                    bucket_key=bucket_key - i,
                    bucket_count=value,
                    cleanup_timestamp=timezone.now() + datetime.timedelta(seconds=10),
                )

    def test_nominal(self):
        limiter = Limiter("test", "10/min")
        self.set_history(limiter, "client_key", [1, 0, 2, 1, 0, 1, 0, 4])
        assert limiter.rate_limit_waiting_time("client_key") == 0

        self.set_history(limiter, "client_key2", [1, 0, 2, 1, 0, 1, 0, 4, 1])
        # We have to wait until 9th (or 10th) bucket is dropped from the sliding window
        assert limiter.rate_limit_waiting_time("client_key2") in (
            limiter.window_seconds - 8 * limiter.bucket_seconds,
            limiter.window_seconds - 9 * limiter.bucket_seconds,
        )

        self.set_history(limiter, "client_key3", [3, 0, 2, 1, 0, 1, 0, 4, 1, 10])
        # We have to wait until 8th (or 9th) bucket is dropped from the sliding window
        assert limiter.rate_limit_waiting_time("client_key3") in (
            limiter.window_seconds - 7 * limiter.bucket_seconds,
            limiter.window_seconds - 8 * limiter.bucket_seconds,
        )

    def test_full(self):
        limiter = Limiter("test", "10/min")
        self.set_history(limiter, "client_key", [9])
        assert limiter.rate_limit_waiting_time("client_key") == 0
        assert limiter.rate_limit_waiting_time("client_key") in (
            limiter.window_seconds,
            limiter.window_seconds - limiter.bucket_seconds,
        )


@pytest.mark.django_db(transaction=True)
def test_concurrent_rate_limit():
    limiter = Limiter("test", rate="12/min")

    def simulate_call(_i):
        result = limiter.rate_limit_waiting_time("test_key")
        connection.close()  # Avoid FATAL postgresql error: sorry, too many clients already
        return result

    pool = multiprocessing.pool.ThreadPool(10)
    result = collections.Counter(pool.map(simulate_call, range(100)))
    assert result[0] == 12
    assert result[60] + result[60 - 2] == 88, result


def test_cleanup():
    limiter = Limiter("test", rate="10/min")
    limiter.rate_limit_waiting_time("test_key")
    assert RateLimitCounter.objects.count() == 1
    call_command("cleanup_obsolete_buckets")
    assert RateLimitCounter.objects.count() == 1

    RateLimitCounter.objects.create(
        limiter_key="foo",
        client_key="bar",
        bucket_key=int(time.time() / 2) - 3 * 30,
        bucket_count=1,
        cleanup_timestamp=(
            timezone.now() - datetime.timedelta(seconds=5)  # In case of a drift between python and postgresql clocks
        ),
    )
    assert RateLimitCounter.objects.count() == 2
    call_command("cleanup_obsolete_buckets")
    assert RateLimitCounter.objects.count() == 1


def test_inside_transaction():
    limiter = Limiter("test", rate="10/min")
    with (
        transaction.atomic(),
        pytest.raises(RuntimeError, match="This function isn't meant to be called from inside a transaction"),
    ):
        limiter.rate_limit_waiting_time("test_key")
