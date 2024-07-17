import asyncio
from typing import Any
from asyncio import Future

from playwright.async_api import Browser, Response

from octo.core import Crawler
from octo.datasource import DatasourceRedis
from octo.parser import Parser, ParseNode, ParseStep, ParseResponse
from octo.storage import FileStorage

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
        await page.goto(book_url, wait_until="domcontentloaded")

        similar_books_fut = asyncio.Future()
        page.on("response", is_similar_books_resp(similar_books_fut))

        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        
        try:
            await asyncio.wait_for(similar_books_fut, timeout=1)
            fut.result()
        except:
            pass
        parse_response.html = await page.content()

        return parse_response

async def main():
    ds = DatasourceRedis()
    storage = FileStorage("books.txt")

    pre = [PreStep()]
    parser = Parser(parse_steps=pre)

    crawler = Crawler(
        ds,
        parser,
        storage,
        sleep_for=1,
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
