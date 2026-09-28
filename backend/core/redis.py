import json

import redis

from core.config import settings


redis_client = redis.Redis.from_url(
    settings.redis_url,
    decode_responses=True,
)


def save_trip_state(
    trip_id: str,
    state: dict,
    expire_seconds: int = 86400,
) -> None:
    key = f"travelai:trip:{trip_id}"

    redis_client.set(
        key,
        json.dumps(state, default=str),
        ex=expire_seconds,
    )


def get_trip_state(trip_id: str) -> dict | None:
    key = f"travelai:trip:{trip_id}"

    value = redis_client.get(key)

    if value is None:
        return None

    return json.loads(value)


def delete_trip_state(trip_id: str) -> None:
    key = f"travelai:trip:{trip_id}"
    redis_client.delete(key)


def redis_health_check() -> bool:
    try:
        return bool(redis_client.ping())
    except redis.RedisError:
        return False