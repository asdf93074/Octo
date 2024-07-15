from typing import Dict, List
from crawler.parser import ParseNode


def parse_document(html: str, parse_arr: List[ParseNode]) -> Dict[str, str] | None:
    if len(parse_arr) == 0:
        return None

    soup = BS(html, "html.parser")
    info = {}
    for pn in parse_arr:
        elements = soup.select(pn.selector)
        if not pn.multiple:
            elements = elements[:1]

        if pn.property == "text":
            values = [el.text.strip() for el in elements]
        else:
            attr = pn.property.split("_")[1]
            values = [el.get(attr) for el in elements]

        info[pn.key] = values[0] if not pn.multiple else values

    return info
