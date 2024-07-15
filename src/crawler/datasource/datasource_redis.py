import redis 

from crawler.datasource import Datasource

class DatasourceRedis(Datasource):
    def __init__(self):
        self.client = redis.Redis(
            host="localhost", port=6380, decode_responses=True, db=0, password="mypassword"
        )

    def get_client(self):
        return self.client
