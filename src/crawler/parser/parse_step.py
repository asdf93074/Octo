from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Dict, Any

from playwright.async_api import Browser


class ParseResponse:
    name: str | None
    map: Dict[Any, Any] = {}
    html: str | None


class PreParseStep(ABC):
    @abstractmethod
    async def run(
        self, browser: Browser, context: Any, parse_response: ParseResponse
    ) -> Any:
        pass


class ParseStep(ABC):
    @abstractmethod
    async def run(
        self, browser: Browser, context: Any, parse_response: ParseResponse
    ) -> ParseResponse:
        pass


class PostParseStep(ABC):
    @abstractmethod
    async def run(
        self, browser: Browser, context: Any, parse_response: ParseResponse
    ) -> ParseResponse:
        pass
