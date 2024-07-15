import random
import asyncio
import logging
import json
import os
from time import sleep

import redis
from bs4 import BeautifulSoup as BS

from crawler.constants import *
from crawler.book_model import *
from crawler.get_similar_books import get_similar_books
from crawler.datasource import DatasourceRedis
from crawler.core import ParseNode


logging.basicConfig(
    format="%(asctime)s -- %(levelname)s  --  %(filename)s:%(lineno)s -- %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
    filename=os.path.join(os.getcwd(), "logs/url_scrapper.log"),
    level=logging.getLevelName(os.getenv("LOG_LEVEL") or logging.INFO),
)
logger = logging.getLogger(__name__)

ds = DatasourceRedis() 

db.connect()
db.create_tables([Book])

async def get_next_url_from_redis():
    url = None 
    logger.debug("Looking for URL in set...")
    retry_count = 0
    while url == None and retry_count < GET_URL_RETRY:
        url = ds.get() 

        if url != None:
            locked = ds.lock(url) 
            if not locked:
                logger.debug(f"Failed to acquire lock for {url}.")
                url = None

        if url == None:
            logger.debug(f"Attempt {retry_count} / {GET_URL_RETRY}. No URLs found.")
            retry_count += 1
            await asyncio.sleep(1)

    if url != None:
        logger.debug(f"Got URL {url}")
        logger.debug("Moved url to processing set.")
    return url

async def scrape(url):
    books, html = await get_similar_books(url)
    logger.debug(f"Fetched similar books and html for url: {url}")
    return books, html

def parse_document(soup, parse_arr):
    info = {}
    for pn in parse_arr:
        elements = soup.select(pn.selector)
        if not pn.multiple:
            elements = elements[:1]

        if pn.property == "text":
            values = [el.text.strip() for el in elements]
        else:
            attr = pn.property.split("_")[1]
            values = [el.get(attr) for el in elements]

        info[pn.key] = values[0] if not pn.multiple else values
    return info

goodreads_parses = [
    ParseNode("title",          ".BookPageTitleSection__title h1", "text", False),
    ParseNode("imgUrl",         ".BookCover__image img", "attribute_src", False),
    ParseNode("author",         ".ContributorLink__name", "text", False),
    ParseNode("description",    ".DetailsLayoutRightParagraph", "text", False),
    ParseNode("genres",         ".BookPageMetadataSection__genres .BookPageMetadataSection__genreButton", "text", True),
]

async def process_url(url):
    books, raw_html = await scrape(url)
    soup = BS(raw_html, "html.parser")

    logger.debug(f"Parsing {url} for book info.")
    info = parse_document(soup, goodreads_parses)

    logger.debug(f"Finished parsing for {url}:\n {json.dumps(info, indent=2)}")
    logger.debug("Adding to db.")
    book_info = Book(title=info["title"], imgUrl=info["imgUrl"], author=info["author"],
                     description=info["description"], genres=','.join(info["genres"]), url=url)
    if book_info.save() != 1:
        logger.error(f"Error while saving record {book_info}")
    else:
        logger.info("Committed to db.")

    logger.debug("Adding new books to urls set.")
    # logger.info(books)
    for book in books:
        u = book["webUrl"]
        ds.add(u) 

    logger.info("Finished adding new books to urls set.")

    if ds.client.smove(REDIS_PROCESSING_URLS_SET_KEY, REDIS_PROCESSED_URLS_SET_KEY, value=url):
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
            if url == None:
                logger.debug("Failed to get a URL to process, try again later.")
                break

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

