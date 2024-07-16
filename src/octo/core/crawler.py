import random
import asyncio
import logging
import json
import os
from time import sleep
from typing import Any, List

import redis
from bs4 import BeautifulSoup as BS
from playwright.async_api import async_playwright, Browser

from octo.constants import *
from octo.datasource import Datasource
from octo.parser import Parser, ParseNode, parse_document


logging.basicConfig(
    format="%(asctime)s -- %(levelname)s  --  %(filename)s:%(lineno)s -- %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
    filename=os.path.join(os.getcwd(), "logs/url_scrapper.log"),
    level=logging.getLevelName(os.getenv("LOG_LEVEL") or logging.INFO),
)
logger = logging.getLogger(__name__)


class Crawler:
    def __init__(
        self,
        datasource: Datasource,
        parser: Parser,
        storage: Any,
        sleep_for: int | List[int] = [8, 15],
        parse_nodes: List[ParseNode] = [],
    ):

        self._sleep_for = sleep_for
        self._parse_nodes = parse_nodes

        self._ds_client = datasource
        self._storage_client = storage
        self._parser = parser

    async def __aenter__(self):
        logger.debug("Initializing playwright for Crawler.")
        proxy = None
        if os.getenv("HTTPS_PROXY"):
            proxy = {"server": os.getenv("HTTPS_PROXY")}

        self._playwright_context_manager = await async_playwright().__aenter__()
        self._browser = await self._playwright_context_manager.chromium.launch(proxy=proxy, headless=True)

    async def __aexit__(self):
        logger.debug("Closing playwright context for Crawler.")
        self._playwright_context_manager.__aexit__()

    def _get_sleep_time(self):
        if type(self._sleep_for) == int:
            return self._sleep_for

        if type(self._sleep_for) == list:
            min_sleep = self._sleep_for[0]
            max_sleep = self._sleep_for[1]

            return random.randint(min_sleep, max_sleep)
        else:
            raise TypeError("Invalid sleep time passed in config for Crawler.")

    async def _get_next_url_from_datasource(self):
        url = None
        logger.debug("Looking for URL in set...")
        retry_count = 0
        while url == None and retry_count < GET_URL_RETRY:
            url = self._ds_client.get()

            if url != None:
                locked = self._ds_client.lock(url)
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

    async def _scrape(self, url):
        parse_response = await self._parser.parse(self._browser, {"url": url})

        return parse_response

    async def process_url(self, url):
        parse_response = await self._scrape(url)
        info = parse_document(parse_response.html, self._parse_nodes)

        logger.debug(f"Finished parsing for {url}:\n {json.dumps(info, indent=2)}")
        logger.debug("Writing to storage.")

        # self._storage_client.save(info)

        if self._ds_client.client.smove(
            REDIS_PROCESSING_URLS_SET_KEY, REDIS_PROCESSED_URLS_SET_KEY, value=url
        ):
            logger.debug(f"Moved {url} to processed set.")
        else:
            logger.debug(
                f"Failed to moved {url} to processed set. Was it already processed somewhere else?"
            )

    async def start(self):
        background_tasks = set()
        logger.info("Starting URL scrapper.")

        # get new urls to crawl
        logger.info("Fetching new URL from redis.")
        while True:
            url = None
            try:
                url = await self._get_next_url_from_datasource()
                if url == None:
                    logger.debug("Failed to get a URL to process, try again later.")
                    break

                proc_task = asyncio.create_task(
                    self.process_url(url), name=f"Task-{url.split("/")[-1]}"
                )

                background_tasks.add(proc_task)
                proc_task.add_done_callback(background_tasks.discard)

                logger.info(f"Queued processing for URL: {url}.")
            except Exception as e:
                logger.error(f"Error while processing URL: {url}, error: {e}")
            finally:
                s = self._get_sleep_time()
                logger.debug(
                    f"Sleeping for {s}s before queuing next URL to rate-limit..."
                )
                await asyncio.sleep(s)
