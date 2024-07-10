import asyncio
import json
import os

from playwright.async_api import async_playwright


async def get_similar_books(book_url):
    async with async_playwright() as p:
        proxy = None
        if os.getenv('HTTPS_PROXY'):
            proxy = { 'server': os.getenv('HTTPS_PROXY') }
        browser = await p.chromium.launch(proxy=proxy, headless=True)
        page = await browser.new_page()
        similar_books = []
        parsed_books = False

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
                        parsed_books = True
                except:
                    pass

        page.on("response", handle_response)
        await page.goto(book_url, wait_until='domcontentloaded')
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(2000)
        html = await page.content()
        
        # wait 10s to get the getSimilarBooks API response
        s = 0 
        while not parsed_books and s < 10:
            await asyncio.sleep(1)
            s += 1

        await browser.close()

        return [similar_books, html]

async def main():
    url = "https://www.goodreads.com/book/show/3.Harry_Potter_and_the_Sorcerer_s_Stone"
    books, html = await get_similar_books(url)
    print(books)
    print('saving html to hp.html')
    open('hp.html', 'w').write(html)

    if len(books) == 0:
        print("No book URLs were scrapped.")
        return

    for book in books:
        print(f"Title: {book['title']}")
        print(f"URL: {book['webUrl']}")
        print()

if __name__ == "__main__":
    asyncio.run(main())
