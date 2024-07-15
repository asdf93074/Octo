from dataclasses import dataclass
from typing import List

from playwright.async_api import Browser
from crawler.parser import ParseResponse, ParseStep, PreParseStep, PostParseStep


class Parser:
    def __init__(
        self,
        pre_steps: List[PreParseStep] | None = [],
        post_steps: List[PostParseStep] | None = [],
        parse_steps: List[ParseStep] | None = [],
    ) -> None:
        self._pre_steps = pre_steps
        self._post_steps = post_steps
        self._parse_steps = parse_steps

    async def _pre(self, browser: Browser, parse_response: ParseResponse) -> None:
        context = None
        for s in self._pre_steps:
            context = await s.run(browser, context, parse_response)

    async def parse(self, browser: Browser) -> ParseResponse:
        pr = ParseResponse()

        await self._pre(browser, pr)

        context = None
        for s in self._parse_steps:
            context = await s.run(browser, context, pr)

        await self._post(browser, pr)

        return pr

    async def _post(self, browser: Browser, parse_response: ParseResponse) -> None:
        context = None
        for s in self._post_steps:
            context = await s.run(browser, context, parse_response)
