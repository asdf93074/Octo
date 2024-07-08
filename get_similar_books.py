from playwright.sync_api import sync_playwright
import json

def get_similar_books(book_url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        similar_books = []

        def handle_response(response):
            if response.request.url.endswith('/graphql') and response.request.method == 'POST':
                try:
                    body = response.json()
                    if 'data' in body and 'getSimilarBooks' in body['data']:
                        for edge in body['data']['getSimilarBooks']['edges']:
                            book = edge['node']
                            similar_books.append({
                                'title': book['title'],
                                'webUrl': book['webUrl']
                            })
                except:
                    pass

        page.on('response', handle_response)
        page.goto(book_url)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(5000)
        browser.close()

        return similar_books

if __name__ == "__main__":
    url = "https://www.goodreads.com/book/show/3.Harry_Potter_and_the_Sorcerer_s_Stone"
    books = get_similar_books(url)
    for book in books:
        print(f"Title: {book['title']}")
        print(f"URL: {book['webUrl']}")
        print()
