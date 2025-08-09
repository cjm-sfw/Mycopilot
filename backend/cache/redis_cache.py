import redis
import json
from typing import Optional, Dict, Any
from backend.config import settings

class RedisCache:
    def __init__(self):
        self.client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db
        )
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve a paper from cache"""
        cached = self.client.get(key)
        if cached:
            return json.loads(cached)
        return None
    
    def set(self, key: str, value: Dict[str, Any], ttl: int = 86400):
        """Store a paper in cache with TTL (default: 24 hours)"""
        self.client.setex(key, ttl, json.dumps(value))
    
    def delete(self, key: str):
        """Remove a paper from cache"""
        self.client.delete(key)
    
    def clear(self):
        """Clear all cached papers"""
        self.client.flushdb()

# Global cache instance
cache = RedisCache()
