from dataclasses import dataclass


@dataclass
class ParseNode:
    """Defines what and how to parse and what form the parsed data should take."""

    key: str
    selector: str
    property: str
    multiple: bool
