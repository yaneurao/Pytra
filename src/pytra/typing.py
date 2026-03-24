"""Pytra typing module — re-exports from Python standard typing.

Python runtime: standard typing functions are available.
Transpiler: recognizes these type names natively for annotation purposes.
"""

from typing import *  # noqa: F401,F403

# Iterator[T] / Iterable[T] は typing から re-export 済みだが、
# トランスパイラが認識できるよう明示的にここで宣言する。
# Python 実行時は typing.Iterator がそのまま使われる。
# トランスパイル時は resolve が Iterator[T] の T を要素型として解決する。
# Iterator の実装は各言語の runtime が提供する。
