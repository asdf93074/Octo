import random
import asyncio
import logging
import json
from time import sleep

import redis
from bs4 import BeautifulSoup as BS

from get_similar_books import get_similar_books
from constants import *
from book_model import *

logging.basicConfig(
    format="%(asctime)s -- %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
    filename="logs/url_scrapper.log",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

r = redis.Redis(
    host="localhost", port=6380, decode_responses=True, db=0, password="mypassword"
)

db.connect()
db.create_tables([Book])

async def get_next_url_from_redis():
    url = None 
    logger.debug("Looking for URL in set...")
    while url == None:
        url = r.srandmember(REDIS_URLS_SET_KEY)
        if url != None:
            moved = r.smove(REDIS_URLS_SET_KEY, REDIS_PROCESSING_URLS_SET_KEY, value=url)
            if not moved:
                url = None
            else:
                logger.info(f"Got URL {url}")
                logger.debug("Moved url to processing set.")
        else:
            logger.debug("No URLs found in set. Sleeping and trying again in a bit...")
            await asyncio.sleep(1)

    return url

async def scrape(url):
    books, html = await get_similar_books(url)
    logger.debug(f"Fetched similar books and html for url: {url}")
    return books, html


def create_parse_node(selector, property, multiple=False):
    return {"selector": selector, "property": property, "multiple": multiple}

def parse_document(soup, parse_dict):
    info = {}
    for key, node in parse_dict.items():
        elements = soup.select(node["selector"])
        if not node["multiple"]:
            elements = elements[:1]

        if node["property"] == "text":
            values = [el.text.strip() for el in elements]
        else:
            attr = node["property"].split("_")[1]
            values = [el.get(attr) for el in elements]

        info[key] = values[0] if not node["multiple"] else values
    return info

goodreads_parse_dict = {
    "title": create_parse_node(".BookPageTitleSection__title h1", "text"),
    "imgUrl": create_parse_node(".BookCover__image img", "attribute_src"),
    "author": create_parse_node(".ContributorLink__name", "text"),
    "description": create_parse_node(".DetailsLayoutRightParagraph", "text"),
    "genres": create_parse_node(
        ".BookPageMetadataSection__genres .BookPageMetadataSection__genreButton",
        "text",
        True,
    ),
}

async def process_url(url):
    books, raw_html = await scrape(url)
    soup = BS(raw_html, "html.parser")

    logger.debug(f"Parsing {url} for book info.")
    info = parse_document(soup, goodreads_parse_dict)

    logger.debug(f"Finished parsing for {url}:\n {json.dumps(info, indent=2)}")
    logger.info("Adding to db.")
    book_info = Book(title=info["title"], imgUrl=info["imgUrl"], author=info["author"],
                     description=info["description"], genres=','.join(info["genres"]), url=url)
    if book_info.save() != 1:
        logger.error(f"Error while saving record {book_info}")
    else:
        logger.info("Committed to db.")

    logger.info("Adding new books to urls set.")
    # logger.info(books)
    for book in books:
        u = book["webUrl"]
        r.sadd(REDIS_URLS_SET_KEY, u)

    logger.info("Finished adding new books to urls set.")

    if r.smove(REDIS_PROCESSING_URLS_SET_KEY, REDIS_PROCESSED_URLS_SET_KEY, value=url):
        logger.debug(f"Moved {url} to processed set.")
    else:
        logger.debug(f"Failed to moved {url} to processed set. Was it already processed somewhere else?")

async def start():
    background_tasks = set()
    logger.info("Starting URL scrapper.")

    # get new urls to crawl
    logger.info("Fetching new URL from redis.")
    while True:
        url = None
        try:
            url = await get_next_url_from_redis()
            proc_task = asyncio.create_task(process_url(url), name=f"Task-{url.split("/")[-1]}")

            background_tasks.add(proc_task)
            proc_task.add_done_callback(background_tasks.discard)

            logger.info(f"Queued processing for URL: {url}.")
        except Exception as e:
            logger.error(f"Error while processing URL: {url}, error: {e}")
        finally:
            s = random.randint(8, 15)
            logger.debug(f"Sleeping for {s}s before queuing next URL to rate-limit...")
            await asyncio.sleep(s)


if __name__ == "__main__":
    asyncio.run(start())
