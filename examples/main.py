import random
import asyncio
import logging
import json
import os
from typing import Any
from time import sleep
from asyncio import Future

import redis
from bs4 import BeautifulSoup as BS
from playwright.async_api import async_playwright, Browser, Response

from octo.parser import Parser, ParseNode, ParseStep, ParseResponse
from octo.constants import *
from octo.datasource import DatasourceRedis
from octo.core import Crawler

from book_model import *

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

def is_similar_books_resp(fut: Future):
    async def wrapper(response: Response):
        if response.request.url.endswith("/graphql") and response.request.method == "POST":
            body = await response.json()
            if "data" in body and "getSimilarBooks" in body["data"]:
                fut.set_result(body["data"]["getSimilarBooks"])
    return wrapper

class PreStep(ParseStep):
    async def run(
        self, browser: Browser, context: Any, parse_response: ParseResponse
    ) -> ParseResponse:
        book_url = context["url"]
        page = await browser.new_page()

        similar_books_fut = asyncio.Future()
        page.on("response", is_similar_books_resp(similar_books_fut))
        await page.goto(book_url, wait_until="domcontentloaded")
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        
        try:
            await asyncio.wait_for(similar_books_fut, timeout=10)
            fut.result()
        except:
            logger.error("Could not get similar books.")
        parse_response.html = await page.content()

        return parse_response

async def main():
    ds = DatasourceRedis()
    pre = [PreStep()]
    parser = Parser(parse_steps=pre)
    crawler = Crawler(
        ds,
        parser,
        None,
        parse_nodes=[
            ParseNode("urls", ".BookCard__clickCardTarget.BookCard__interactive.BookCard__block", "attribute_href", True),
            ParseNode("title", ".BookPageTitleSection__title h1", "text", False),
            ParseNode("imgUrl", ".BookCover__image img", "attribute_src", False),
            ParseNode("author", ".ContributorLink__name", "text", False),
            ParseNode("description", ".DetailsLayoutRightParagraph", "text", False),
            ParseNode(
                "genres",
                ".BookPageMetadataSection__genres .BookPageMetadataSection__genreButton",
                "text",
                True,
            ),
        ],
    )

    async with crawler:
        await crawler.start()

if __name__ == "__main__":
    asyncio.run(main())

    # books, raw_html = await scrape(url)
    # soup = BS(raw_html, "html.parser")

    # logger.debug(f"Parsing {url} for book info.")
    # info = parse_document(soup, goodreads_parses)

    # logger.debug(f"Finished parsing for {url}:\n {json.dumps(info, indent=2)}")
    # logger.debug("Adding to db.")
    # book_info = Book(
    #     title=info["title"],
    #     imgUrl=info["imgUrl"],
    #     author=info["author"],
    #     description=info["description"],
    #     genres=",".join(info["genres"]),
    #     url=url,
    # )
    # if book_info.save() != 1:
    #     logger.error(f"Error while saving record {book_info}")
    # else:
    #     logger.info("Committed to db.")

    # logger.debug("Adding new books to urls set.")
    # # logger.info(books)
    # for book in books:
    #     u = book["webUrl"]
    #     ds.add(u)

    # logger.info("Finished adding new books to urls set.")

    # if ds.client.smove(
    #     REDIS_PROCESSING_URLS_SET_KEY, REDIS_PROCESSED_URLS_SET_KEY, value=url
    # ):
    #     logger.debug(f"Moved {url} to processed set.")
    # else:
    #     logger.debug(
    #         f"Failed to moved {url} to processed set. Was it already processed somewhere else?"
    #     )
