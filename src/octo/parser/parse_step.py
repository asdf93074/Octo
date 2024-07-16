from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Dict, List, Any

from playwright.async_api import Browser


class ParseResponse:
    name: str | None
    map: Dict[Any, Any] = {}
    html: str | None
    urls: List[str]

class ParseStep(ABC):
    @abstractmethod
    async def run(
        self, browser: Browser, context: Any, parse_response: ParseResponse
    ) -> ParseResponse:
        pass
