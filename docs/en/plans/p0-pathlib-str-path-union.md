<a href="../../ja/plans/p0-pathlib-str-path-union.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/p0-pathlib-str-path-union.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/p0-pathlib-str-path-union.md`

# P0: pathlib.Path の __init__ / __truediv__ を str | Path 対応に修正

最終更新: 2026-03-19

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-PATHLIB-STR-PATH-UNION-01`

## 背景

Python 標準の `pathlib.Path` は `Path(other_path)` や `path1 / path2` を受け付ける。
Pytra の `src/pytra/std/pathlib.py` は `__init__(value: str)` と `__truediv__(rhs: str)` で
`str` のみ受け付けており、`Path` を渡せない。

以前 `str | Path` に変更を試みたが、当時は inline union が `std::variant` で生成されており
一貫性がなかったため revert した。P0-INLINE-UNION-TAGGED-STRUCT-01 が完了し
inline union が tagged struct で生成されるようになったため、再度実施可能。

## 修正内容

```python
def __init__(self, value: str | Path) -> None:
    if isinstance(value, Path):
        self._value = cast(Path, value)._value
    else:
        self._value = cast(str, value)

def __truediv__(self, rhs: str | Path) -> Path:
    if isinstance(rhs, Path):
        return Path(path.join(self._value, cast(Path, rhs)._value))
    return Path(path.join(self._value, cast(str, rhs)))
```

## 対象

- `src/pytra/std/pathlib.py` — `__init__` / `__truediv__` を `str | Path` に変更
- `src/runtime/cpp/generated/std/pathlib.h` / `.cpp` — 再生成

## 受け入れ基準

- `Path("foo")` と `Path(other_path)` が動作する。
- `path1 / path2` と `path1 / "str"` が動作する。
- C++ 生成コードで inline tagged struct（`_Union_str_Path` 等）が生成される。
- Python 実行時にも動作する。
- fixture / sample pass。

## 決定ログ

- 2026-03-19: P0-INLINE-UNION-TAGGED-STRUCT-01 完了に伴い再起票。cast() による型ナローイングで実装。
