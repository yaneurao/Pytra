"""SourceSpan: ソースコード位置情報。

§5.1: Any/object 禁止。JsonVal 互換の dict を返す。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from pytra.std.json import JsonVal


@dataclass
class SourceSpan:
    """ソースコード上の位置範囲。"""

    lineno: Optional[int]
    col: Optional[int]
    end_lineno: Optional[int]
    end_col: Optional[int]

    def to_jv(self) -> dict[str, JsonVal]:
        out: dict[str, JsonVal] = {}
        if self.lineno is None:
            out["lineno"] = None
        else:
            out["lineno"] = int(self.lineno)
        if self.col is None:
            out["col"] = None
        else:
            out["col"] = int(self.col)
        if self.end_lineno is None:
            out["end_lineno"] = None
        else:
            out["end_lineno"] = int(self.end_lineno)
        if self.end_col is None:
            out["end_col"] = None
        else:
            out["end_col"] = int(self.end_col)
        return out


NULL_SPAN = SourceSpan(lineno=None, col=None, end_lineno=None, end_col=None)


def make_span(lineno: int, col: int, end_lineno: int, end_col: int) -> SourceSpan:
    return SourceSpan(lineno=lineno, col=col, end_lineno=end_lineno, end_col=end_col)
