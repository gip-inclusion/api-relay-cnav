from django.db import connection


class Limiter:
    def __init__(self, key: str, rate: str) -> None:
        self.key = key
        self._rate = rate
        self.window_limit, self.window_seconds, self.bucket_seconds = self.parse_rate(rate)

    @staticmethod
    def parse_rate(rate: str) -> tuple[int, int, int]:
        num, period = rate.split("/")
        num_requests = int(num)
        window_seconds = {"s": 1, "m": 60, "h": 3600, "d": 86400}[period[0]]
        bucket_seconds = {"s": 1, "m": 2, "h": 120, "d": 3600}[period[0]]
        return (num_requests, window_seconds, bucket_seconds)

    def rate_limit_waiting_time(self, key: str) -> int:
        if any(not atomic_block._from_testcase for atomic_block in connection.atomic_blocks):
            raise RuntimeError("This function isn't meant to be called from inside a transaction")
        with connection.cursor() as cursor:
            cursor.execute(
                """
                WITH current_bucket AS (
                    SELECT (extract(epoch FROM now())::bigint / %s) AS bkey
                ),
                increment AS (
                    INSERT INTO rate_limit_ratelimitcounter
                        (limiter_key, client_key, bucket_key, bucket_count, cleanup_timestamp)
                    VALUES (%s, %s, (SELECT bkey FROM current_bucket), 1, now() + interval '1 second' * (%s + 60))
                    ON CONFLICT (limiter_key, client_key, bucket_key)
                    DO UPDATE SET bucket_count = rate_limit_ratelimitcounter.bucket_count + 1
                    RETURNING bucket_count
                ),
                history AS (
                    (SELECT bucket_key, bucket_count
                     FROM rate_limit_ratelimitcounter
                     WHERE limiter_key = %s
                       AND client_key = %s
                       AND bucket_key >= (
                           SELECT bkey - %s FROM current_bucket
                       )
                       AND bucket_key < (SELECT bkey FROM current_bucket)
                    )
                    UNION
                    (
                     SELECT
                       (SELECT bkey FROM current_bucket) as bucket_key,
                       (SELECT bucket_count FROM increment) as bucket_count
                    )
                ),
                cumulated_history AS (
                  SELECT
                    bucket_key,
                    bucket_count,
                    SUM(bucket_count) OVER (ORDER BY bucket_key DESC) AS cumulative_sum,
                    %s - ((SELECT bkey FROM current_bucket) - bucket_key) * %s AS waiting_time
                  FROM history)
                SELECT waiting_time FROM cumulated_history WHERE cumulative_sum > %s
                ORDER BY bucket_key DESC LIMIT 1;""",
                (
                    self.bucket_seconds,
                    self.key,
                    key,
                    self.window_seconds,
                    self.key,
                    key,
                    self.window_seconds / self.bucket_seconds,
                    self.window_seconds,
                    self.bucket_seconds,
                    self.window_limit,
                ),
            )
            waiting_time = cursor.fetchone()
        return waiting_time[0] if waiting_time is not None else 0


def cleanup_obsolete_buckets() -> None:
    # Use the same postgresql NOW() function instead of timezone.now()
    with connection.cursor() as cursor:
        cursor.execute(
            "DELETE FROM rate_limit_ratelimitcounter WHERE cleanup_timestamp < now();",
        )
