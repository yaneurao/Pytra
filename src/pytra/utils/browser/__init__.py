"""Minimal browser shim for transpilation and non-browser backends."""

from __future__ import annotations


class Touch:
    @property
    def clientX(self) -> int:
        return 0

    @property
    def clientY(self) -> int:
        return 0

    @property
    def identifier(self) -> int:
        return 0


class DOMEvent:
    @property
    def keyCode(self) -> int:
        return 0

    @property
    def offsetX(self) -> int:
        return 0

    @property
    def offsetY(self) -> int:
        return 0

    @property
    def buttons(self) -> int:
        return 0

    @property
    def touches(self) -> list[Touch]:
        return []

    def preventDefault(self) -> None:
        pass

    def stopPropagation(self) -> None:
        pass


class TextMetrics:
    def __init__(self) -> None:
        self.width: int = 0
        self.height: int = 0


class HtmlImage:
    def __init__(self) -> None:
        self.naturalWidth: int = 0
        self.naturalHeight: int = 0

    def __setitem__(self, name: str, value: str) -> "Element":
        _ = name
        _ = value
        return Element()


class CanvasRenderingContext:
    def __init__(self) -> None:
        self.fillStyle: str = ""
        self.strokeStyle: str = ""
        self.font: str = ""
        self.textBaseline: str = ""

    def fillRect(self, x: int | float, y: int | float, w: int | float, h: int | float) -> None:
        _ = x
        _ = y
        _ = w
        _ = h

    def fillText(self, text: str, x: int | float, y: int | float) -> None:
        _ = text
        _ = x
        _ = y

    def strokeRect(self, x: int | float, y: int | float, w: int | float, h: int | float) -> None:
        _ = x
        _ = y
        _ = w
        _ = h

    def drawImage(
        self,
        image: HtmlImage,
        sx: int | float,
        sy: int | float,
        sw: int | float,
        sh: int | float,
        px: int | float,
        py: int | float,
        dw: int | float,
        dh: int | float,
    ) -> None:
        _ = image
        _ = sx
        _ = sy
        _ = sw
        _ = sh
        _ = px
        _ = py
        _ = dw
        _ = dh

    def measureText(self, text: str) -> TextMetrics:
        _ = text
        return TextMetrics()


class ImageCreator:
    def new(self) -> HtmlImage:
        return HtmlImage()


class IntervalHandle:
    pass


class window:
    Image = ImageCreator()

    @staticmethod
    def setInterval(callback: object, t: int | float) -> IntervalHandle:
        _ = callback
        _ = t
        return IntervalHandle()

    @staticmethod
    def clearInterval(handle: IntervalHandle) -> None:
        _ = handle


class Element:
    def __init__(self) -> None:
        self.currentTime: int | float = 0
        self.volume: int | float = 0
        self.width: int = 0
        self.height: int = 0

    def createElement(self, name: str) -> "Element":
        _ = name
        return Element()

    def addEventListener(self, eventName: str, callback: object) -> None:
        _ = eventName
        _ = callback

    def removeEventListener(self, eventName: str, callback: object) -> None:
        _ = eventName
        _ = callback

    def __getitem__(self, name: str) -> "Element":
        _ = name
        return Element()

    def __setitem__(self, name: str, value: str) -> "Element":
        _ = name
        _ = value
        return Element()

    def play(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def pause(self) -> None:
        pass

    def getContext(self, name: str) -> CanvasRenderingContext:
        _ = name
        return CanvasRenderingContext()


document = Element()

