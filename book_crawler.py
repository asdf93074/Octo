from time import sleep
import logging
import json

import requests
from bs4 import BeautifulSoup as BS

from get_similar_books import get_similar_books

logging.basicConfig(
    format="%(asctime)s -- %(message)s",
    datefmt="%m/%d/%Y %I:%M;%S %p",
    filename="logs/crawler.log",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

CRAWL_SLEEP_INTERVAL = 3  # seconds


def create_parse_node(selector, property, multiple=False):
    return {"selector": selector, "property": property, "multiple": multiple}


def get_document_soup(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, timeout=30, verify=False)
    return BS(response.text, "html.parser")


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


def crawl_goodreads(start_urls):
    processed_urls = set()
    urls = set(start_urls)

    while urls:
        url = urls.pop()
        if url in processed_urls:
            continue

        try:
            logger.info(f"Crawling URL: {url}")
            soup = get_document_soup(url)
            info = parse_document(soup, goodreads_parse_dict)
            similar_books = get_similar_books(url)

            logger.info(f"Book info: {json.dumps(info, indent=2)}")
            logger.info(f"Similar books: {json.dumps(similar_books, indent=2)}")

            urls.update([book["webUrl"] for book in similar_books])
            processed_urls.add(url)

            sleep(CRAWL_SLEEP_INTERVAL)
        except Exception as e:
            logger.error(f"Error while crawling URL: {url}", exc_info=True)


if __name__ == "__main__":
    start_urls = [
        "https://www.goodreads.com/book/show/42844155-harry-potter-and-the-sorcerer-s-stone",
    ]
    crawl_goodreads(start_urls)
