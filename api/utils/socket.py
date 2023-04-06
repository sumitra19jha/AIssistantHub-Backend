import requests
import json
from pybreaker import CircuitBreaker, CircuitBreakerError

from api.utils.request import log_response
from api.utils import logging_wrapper
from config import Config

headers = {
    "Authorization": f"Bearer {Config.RTC_AUTH_KEY}",
    "Content-Type": "application/json",
}

logger = logging_wrapper.Logger(__name__)

# Create a circuit breaker object with default settings
breaker = CircuitBreaker()


class Socket:
    @staticmethod
    def create_room_for_content(content_id, user_id):
        assert content_id is not None
        assert user_id is not None

        url = f"{Config.RTC_URL}room/create-room"
        body = {"contentId": content_id, "userId": user_id}
        try:
            res = requests.post(url, data=json.dumps(body), headers=headers, timeout=5)
            log_response(res)
        except Exception as e:
            logger.exception(str(e))