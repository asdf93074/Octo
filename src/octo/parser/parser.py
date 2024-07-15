from dataclasses import dataclass
from typing import List, Any

from playwright.async_api import Browser
from octo.parser import ParseResponse, ParseStep


class Parser:
    def __init__(
        self,
        parse_steps: List[ParseStep] | None = [],
    ) -> None:
        self._parse_steps = parse_steps

    async def parse(self, browser: Browser, context: Any) -> ParseResponse:
        pr = ParseResponse()

        for s in self._parse_steps:
            context = await s.run(browser, context, pr)

        return pr
