from typing import Callable, Optional

from nicegui.element import Element


class NWB(Element, component="nwb.js"):

    def __init__(self, path: str, *, on_change: Optional[Callable] = None) -> None:
        super().__init__()
        self._props["path"] = path
        self.on("change", on_change)

    def reset(self) -> None:
        self.run_method("reset")

    def display(self, coords) -> None:
        self.run_method("display", coords)
