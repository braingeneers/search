from typing import Callable, Optional

from nicegui.element import Element


class NWB(Element, component="nwb.js"):

    def __init__(self, url: str, path: str) -> None:
        super().__init__()
        self._props["url"] = url
        self._props["path"] = path

    def display(self, channels, start, duration) -> None:
        self.run_method("display", channels, start, duration)