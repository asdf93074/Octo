import json
from typing import Any

from octo.storage import Storage

class FileStorage(Storage):
    def __init__(self, filename: str):
        if filename == None:
            raise ValueError("No filename passed to FileStorage.")

        self._filename = filename
        self._f = open(filename, "w+")

    def id(self) -> str:
        return f"FileStorage({self._filename})"

    def write(self, data: Any) -> bool | None:
        w = self._f.write(json.dumps(data, indent=2))
        return w > 0
