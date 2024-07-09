from time import sleep
import redis
import asyncio
import logging

from get_similar_books import get_similar_books
from constants import *

logging.basicConfig(
    format="%(asctime)s -- %(message)s",
    datefmt="%m/%d/%Y %I:%M;%S %p",
    filename="logs/url_scrapper.log",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

r = redis.Redis(
    host="localhost", port=6380, decode_responses=True, db=0, password="mypassword"
)

async def get_next_url_from_redis():
    url = r.srandmember(REDIS_URLS_SET_KEY)
    while url == None:
        logger.info("No URLs found in set. Sleeping and trying again in a bit...")
        sleep(0.5)
        url = r.srandmember(REDIS_URLS_SET_KEY)
        moved = r.smove(REDIS_URLS_SET_KEY, REDIS_PROCESSING_URLS_SET_KEY, value=url)
        if not moved:
            url = None
        else:
            logger.info(f"Got URL {url}")
            logger.info("Moved url to processing set.")

    return url


async def scrape(url):
    books = await get_similar_books(url)
    logger.info(f"Fetched similar books for url: {url}")
    return books


async def process_url(url):
    books = await scrape(url)

    logger.info("Adding new books to urls set.")
    # logger.info(books)
    for book in books:
        u = book["webUrl"]
        r.sadd(REDIS_URLS_SET_KEY, u)

    logger.info("Finished adding new books to urls set.")

    r.smove(REDIS_PROCESSING_URLS_SET_KEY, REDIS_PROCESSED_URLS_SET_KEY, value=url)
    logger.info("Moved url to processed set.")


async def main():
    background_tasks = set()
    logger.info("Starting URL scrapper.")

    # get new urls to crawl
    logger.info("Fetching new URL from redis.")
    while True:
        try:
            url = await get_next_url_from_redis()
            proc_task = asyncio.create_task(process_url(url))

            background_tasks.add(proc_task)
            proc_task.add_done_callback(background_tasks.discard)

            logger.info(f"Queued processing for URL: {url}.")
        except e:
            logger.error(f"Error while processing URL: {url}, error: {e}")
        finally:
            logger.info("Sleeping before queuing next URL to rate-limit...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
