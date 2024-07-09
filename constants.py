REDIS_URLS_SET_KEY = "urls"
REDIS_PROCESSING_URLS_SET_KEY = "processing_urls"
REDIS_PROCESSED_URLS_SET_KEY = "processed_urls"
REDIS_URL_INFO_HASH_PREFIX = "urls:"


def get_redis_url_hash_key(url):
    return REDIS_URL_INFO_HASH_PREFIX + url
