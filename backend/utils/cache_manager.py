# backend/utils/cache_manager.py
import redis
import json
from datetime import timedelta

class CacheManager:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        self.cache_ttl = 3600  # 1 hour
    
    def cache_search_results(self, query: str, results: List[Dict]):
        """Cache search results for faster retrieval"""
        cache_key = f"search:{hash(query)}"
        serialized_results = json.dumps(results, default=str)
        self.redis_client.setex(cache_key, self.cache_ttl, serialized_results)
    
    def get_cached_results(self, query: str) -> List[Dict]:
        """Retrieve cached search results"""
        cache_key = f"search:{hash(query)}"
        cached_data = self.redis_client.get(cache_key)
        
        if cached_data:
            return json.loads(cached_data)
        return None
    
    def invalidate_cache(self, pattern: str = "search:*"):
        """Invalidate cache when new documents are added"""
        keys = self.redis_client.keys(pattern)
        if keys:
            self.redis_client.delete(*keys)
