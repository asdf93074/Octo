import requests
import urllib3
import logging
from bs4 import BeautifulSoup as BS

from get_similar_books import get_similar_books

logger = logging.getLogger(__name__)
logging.basicConfig(filename='logs/crawler.log', level=logging.INFO)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

RETRIES = 3
CRAWL_RATE_LIMIT_PER_MIN = 20
CRAWL_SLEEP_INTERVAL = 60 // CRAWL_RATE_LIMIT_PER_MIN

SELECT_ONE_METHOD = 'select_one'
SELECT_MANY_METHOD = 'select'


def create_parse_node(selector, property, count=1):
    assert count >= 1, 'count cannot be less than 1'

    return {
        'selector': selector,
        'property': property,
        'method': SELECT_ONE_METHOD if count == 1 else SELECT_MANY_METHOD
    }

def get_document_soup(url):
    soup = None
    with requests.Session() as s:
        s.headers.update({'User-Agent': 'Mozilla/5.0'})

        raw_html = s.get(url, timeout=30)
        soup = BS(raw_html.text, features="html.parser")
    return soup

def parse_document(html, parse_dict):
    info = []
    
    for parsed_key, node in parse_dict.items():
        data = {}
        prop = node['property']
        findMethodName = node['method']
        findMethod = getattr(doc.css, findMethodName)
        selector = node['selector']

        tag = findMethod(selector)

        if prop == 'text':

            if findMethodName == SELECT_ONE_METHOD:
                data[parsed_key] = tag.text
            elif findMethodName == SELECT_MANY_METHOD:
                data[parsed_key] = list(map(ntot('text'), tag))

        elif prop.startswith('attribute'):

            _, attr = prop.split('_')
            if findMethodName == SELECT_ONE_METHOD:
                data[parsed_key] = tag.get(attr)
            elif findMethodName == SELECT_MANY_METHOD:
                data[parsed_key] = list(map(ntot(attr), tag))

        info.append(data)

    return info

def ntot(prop):
    def a(node):
        return getattr(node, prop) 
    return a


goodreads_parse_dict = {
    'title': create_parse_node('.BookPageTitleSection__title h1', 'text'),
    'imgUrl': create_parse_node('.BookCover__image img', 'attribute_src'),
    'author': create_parse_node('.ContributorLink__name', 'text'),
    'description': create_parse_node('.DetailsLayoutRightParagraph', 'text'),
    'genres': create_parse_node('.BookPageMetadataSection__genres .BookPageMetadataSection__genreButton', 'text', 100),
    # 'publishedAt': '',
}

if __name__ == "__main__":
    logger.info('Starting crawler.')

    processed_urls = set()
    urls = [
        "https://www.goodreads.com/book/show/42844155-harry-potter-and-the-sorcerer-s-stone",
    ]
    urls = set(urls)

    for link in urls:
        try:
            l = f'Crawling URL: {link}'
            logger.info(l)
            print(l)
            doc = get_document_soup(link)
            info = parse_document(doc, goodreads_parse_dict)
            crawlable_book_urls = [b['webUrl'] for b in get_similar_books(link)]

            processed_urls.add(link)
            
            logger.info(info)
            logger.info(crawlable_book_urls)
            logger.info(f'Sleeping for {CRAWL_SLEEP_INTERVAL}s')
        except Exception as e:
            logger.error(f'Error while crawling URL: {link}')
            logger.error(e)
            
