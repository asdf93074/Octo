import redis 

from crawler.constants import REDIS_URLS_SET_KEY, REDIS_PROCESSING_URLS_SET_KEY
from crawler.datasource import Datasource

class DatasourceRedis(Datasource):
    def __init__(self):
        self.client = redis.Redis(
            host="localhost", port=6380, decode_responses=True, db=0, password="mypassword"
        )

    def get_client(self):
        return self.client

    def get(self):
        return self.client.srandmember(REDIS_URLS_SET_KEY)

    def lock(self, url: str):
        if url == None:
            raise ValueError("Tried to lock an empty URL.")
        return self.client.smove(REDIS_URLS_SET_KEY, REDIS_PROCESSING_URLS_SET_KEY, value=url)

    def add(self, url: str):
        return self.client.sadd(REDIS_URLS_SET_KEY, u)
