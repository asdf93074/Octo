import asyncio
import json

from playwright.async_api import async_playwright


async def get_similar_books(book_url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        similar_books = []

        async def handle_response(response):
            if (
                response.request.url.endswith("/graphql")
                and response.request.method == "POST"
            ):
                try:
                    body = await response.json()
                    if "data" in body and "getSimilarBooks" in body["data"]:
                        for edge in body["data"]["getSimilarBooks"]["edges"]:
                            book = edge["node"]
                            similar_books.append(
                                {"title": book["title"], "webUrl": book["webUrl"]}
                            )
                except:
                    pass

        page.on("response", handle_response)
        await page.goto(book_url)
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(5000)
        await browser.close()

        return similar_books


async def main():
    url = "https://www.goodreads.com/book/show/3.Harry_Potter_and_the_Sorcerer_s_Stone"
    books = await get_similar_books(url)
    for book in books:
        print(f"Title: {book['title']}")
        print(f"URL: {book['webUrl']}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
