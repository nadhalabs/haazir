import json
import logging
from typing import Optional, Dict, Any, List, Tuple
import redis
from app.core.config import settings

logger = logging.getLogger(__name__)

# Key names and constants
REDIS_GEO_KEY = "haazir:geo:providers"
REDIS_PRESENCE_PREFIX = "haazir:provider:presence:"
DEFAULT_PROVIDER_TTL_SECONDS = 300  # 5 minutes heartbeat TTL


class RedisService:
    def __init__(self, url: str = None):
        self.url = url or settings.REDIS_URL
        self.client: Optional[redis.Redis] = None
        self._connect()

    def _connect(self):
        try:
            self.client = redis.Redis.from_url(self.url, decode_responses=True)
            self.client.ping()
        except Exception as e:
            logger.warning(f"Failed to connect to Redis at {self.url}: {e}")
            self.client = None

    def is_connected(self) -> bool:
        if not self.client:
            return False
        try:
            return bool(self.client.ping())
        except Exception:
            return False

    def update_provider_location(
        self,
        provider_id: str,
        latitude: float,
        longitude: float,
        presence_status: str = "ONLINE_AVAILABLE",
        service_radius_km: float = 15.0,
        ttl_seconds: int = DEFAULT_PROVIDER_TTL_SECONDS
    ) -> bool:
        """
        Atomically updates live provider location in Redis GEO and metadata hash with TTL.
        """
        if not self.client:
            return False

        try:
            pipe = self.client.pipeline()
            # Redis GEOADD syntax: GEOADD key longitude latitude member
            pipe.geoadd(REDIS_GEO_KEY, (longitude, latitude, str(provider_id)))

            presence_key = f"{REDIS_PRESENCE_PREFIX}{provider_id}"
            data = {
                "provider_id": str(provider_id),
                "latitude": str(latitude),
                "longitude": str(longitude),
                "presence_status": presence_status,
                "service_radius_km": str(service_radius_km),
            }
            pipe.hset(presence_key, mapping=data)
            pipe.expire(presence_key, ttl_seconds)
            pipe.execute()
            return True
        except Exception as e:
            logger.error(f"Error updating provider location in Redis: {e}")
            return False

    def set_provider_presence(
        self,
        provider_id: str,
        presence_status: str,
        ttl_seconds: int = DEFAULT_PROVIDER_TTL_SECONDS
    ) -> bool:
        """
        Updates presence status (e.g. OFFLINE, ONLINE_AVAILABLE, ONLINE_BUSY).
        If OFFLINE, removes provider from Redis GEO index.
        """
        if not self.client:
            return False

        try:
            presence_key = f"{REDIS_PRESENCE_PREFIX}{provider_id}"
            if presence_status == "OFFLINE":
                pipe = self.client.pipeline()
                pipe.zrem(REDIS_GEO_KEY, str(provider_id))
                pipe.delete(presence_key)
                pipe.execute()
            else:
                pipe = self.client.pipeline()
                pipe.hset(presence_key, "presence_status", presence_status)
                pipe.expire(presence_key, ttl_seconds)
                pipe.execute()
            return True
        except Exception as e:
            logger.error(f"Error setting provider presence in Redis: {e}")
            return False

    def get_provider_presence(self, provider_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves current live presence and location.
        Returns None if expired or offline.
        """
        if not self.client:
            return None

        try:
            presence_key = f"{REDIS_PRESENCE_PREFIX}{provider_id}"
            data = self.client.hgetall(presence_key)
            if not data:
                return None
            return {
                "provider_id": data.get("provider_id"),
                "latitude": float(data.get("latitude", 0.0)),
                "longitude": float(data.get("longitude", 0.0)),
                "presence_status": data.get("presence_status"),
                "service_radius_km": float(data.get("service_radius_km", 15.0)),
            }
        except Exception as e:
            logger.error(f"Error fetching provider presence from Redis: {e}")
            return None

    def find_nearby_providers_geo(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 25.0,
        limit: int = 20
    ) -> List[Tuple[str, float]]:
        """
        Queries Redis GEORADIUS / GEOSEARCH for providers within radius_km.
        Returns list of tuples: (provider_id_str, distance_km).
        """
        if not self.client:
            return []

        try:
            # redis-py geosearch
            results = self.client.geosearch(
                REDIS_GEO_KEY,
                longitude=longitude,
                latitude=latitude,
                radius=radius_km,
                unit="km",
                withdist=True,
                sort="ASC",
                count=limit
            )
            # results format: [[member, distance], ...]
            return [(str(item[0]), float(item[1])) for item in results]
        except Exception as e:
            logger.error(f"Error in Redis geosearch: {e}")
            return []

    def remove_provider(self, provider_id: str):
        if not self.client:
            return
        try:
            pipe = self.client.pipeline()
            pipe.zrem(REDIS_GEO_KEY, str(provider_id))
            pipe.delete(f"{REDIS_PRESENCE_PREFIX}{provider_id}")
            pipe.execute()
        except Exception:
            pass


redis_service = RedisService()


def get_redis():
    return redis_service.client


def get_redis_service() -> RedisService:
    return redis_service
