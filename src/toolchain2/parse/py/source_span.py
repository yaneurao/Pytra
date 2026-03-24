"""SourceSpan: ソースコード位置情報。

§5.1: Any/object 禁止。JsonVal 互換の dict を返す。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union

# JsonVal 互換型 (pytra.std.json と同じ定義)
JsonVal = Union[None, bool, int, float, str, list["JsonVal"], dict[str, "JsonVal"]]


@dataclass
class SourceSpan:
    """ソースコード上の位置範囲。"""

    lineno: Optional[int]
    col: Optional[int]
    end_lineno: Optional[int]
    end_col: Optional[int]

    def to_jv(self) -> dict[str, JsonVal]:
        return {
            "lineno": self.lineno,
            "col": self.col,
            "end_lineno": self.end_lineno,
            "end_col": self.end_col,
        }


NULL_SPAN = SourceSpan(lineno=None, col=None, end_lineno=None, end_col=None)


def make_span(lineno: int, col: int, end_lineno: int, end_col: int) -> SourceSpan:
    return SourceSpan(lineno=lineno, col=col, end_lineno=end_lineno, end_col=end_col)
