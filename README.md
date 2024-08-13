# Octo

A (WIP) URL-crawler + scrapper from a script written to crawl goodreads.com.

## Quick Start

Initializer a `Crawler` instance with a:

- `Datasource` to keep track of URLs, comes with a built-in one for redis though provide creds in a more secure manner
- `Storage` to store the parsed results
- `Parser` which is made of `ParseStep` to control how the webpage should be accessed and parsed
- Array of `ParseNode` instances to select specific details to be parsed from the HTML of the page

and then do:

```
async with crawler:
    await crawler.start()
```

## Example

Check `examples` folder for a simple way to use this library until some docs are written.
