"""browser.widgets.dialog shim."""

from __future__ import annotations


class Dialog:
    def __init__(self, title: str = "", ok_cancel: bool = False) -> None:
        self.title = title
        self.ok_cancel = ok_cancel


class EntryDialog:
    def __init__(self, title: str = "", value: str = "") -> None:
        self.title = title
        self.value = value


class InfoDialog:
    def __init__(self, title: str = "", text: str = "") -> None:
        self.title = title
        self.text = text

