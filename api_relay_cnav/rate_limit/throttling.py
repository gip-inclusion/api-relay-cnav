from rest_framework.request import Request
from rest_framework.throttling import BaseThrottle

from api_relay_cnav.rate_limit.limiter import Limiter


class LimiterThrottle(BaseThrottle):
    LIMITER: Limiter

    def allow_request(self, request: Request, view: object) -> bool:
        self.wait_duration = self.LIMITER.rate_limit_waiting_time("unique_user")
        return self.wait_duration == 0

    def wait(self) -> int:
        return self.wait_duration


class BurstThrottle(LimiterThrottle):
    LIMITER = Limiter("burst", rate="200/min")


class LongThrottle(LimiterThrottle):
    LIMITER = Limiter("long", rate="5000/hour")
