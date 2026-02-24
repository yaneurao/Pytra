# Iterable/Iterator 改良仕様（案）

この文書は、Pytra の `for ... in ...` 変換における iterable 判定と実行契約を定義する案である。  
主眼は次の2点。

- EAST が「その値を反復可能として扱えるか」を保持すること。
- `object/Any` の反復を、ランタイムの動的プロトコルで Python 準拠に実行すること。

## 1. 背景

現状の C++ 変換は、`for` を C++ range-for へ直接 lower する経路が中心である。  
この方式は `list[T]` など静的型が明確なケースでは高速だが、次の問題がある。

- `object/Any` に対する `for v in x:` が Python の `iter(x)` / `next(it)` 契約になっていない。
- ユーザー定義 `__iter__` があっても、自動で `for` に接続されないケースがある。
- non-iterable に対して Python 的 `TypeError` を返す契約が弱い。

## 2. 目的

1. EAST に iterable 契約を明示し、後段 codegen の判断を安定化する。  
2. `object/Any` の `for` を Python プロトコル準拠にする。  
3. `list` など静的型確定ケースでは最適化経路（直接 range-for）を維持する。  
4. C++ 以外のターゲットでも同一意味論を保つ。

## 3. 非目標

- `async for` / `__aiter__` / `__anext__` 対応。
- `send/throw/close` を含む generator 完全互換。
- 例外メッセージ文字列の CPython 完全一致（型と発生タイミングの一致を優先）。

## 4. 設計原則

1. Python 意味論優先: `for v in x` は `iter(x)` + 反復 `next()` + `StopIteration` 終了。  
2. `object/Any` 境界は fail-fast: iterable でなければ `TypeError`。  
3. 静的型確定時は最適化優先: 不要な動的ディスパッチを入れない。  
4. 多言語整合: virtual の有無に関係なく同じ観測結果にする。

## 5. EAST 契約

## 5.1 式 trait（追加）

各式ノードに、少なくとも次の情報を持たせる。

- `iterable_trait`: `"yes" | "no" | "unknown"`
- `iter_protocol`: `"static_range" | "runtime_protocol" | "none"`
- `iter_element_type`: 要素型（不明時は `"unknown"`）

判定規則:

- `list[T]`, `tuple[T]`, `set[T]`, `str`, `bytes`, `bytearray` などは `iterable_trait="yes"`。
- `dict[K,V]` は `for v in d:` で `keys()`（要素型 `K`）を反復するものとして扱う。`keys()/items()/values()` も `iterable_trait="yes"`。
- `Any/object` や広い union は `iterable_trait="unknown"` + `iter_protocol="runtime_protocol"`。
- 明確に非 iterable な型は `iterable_trait="no"`。

## 5.2 `For` ノード（拡張）

`For` ノードに次を追加する。

- `iter_mode`: `"static_fastpath" | "runtime_protocol"`
- `iter_source_type`: 反復元の解決型（例: `list[int]`, `object`, `Counter`）
- `iter_element_type`: 要素型（既存推論と整合）

意味:

- `static_fastpath`: codegen は直接 range-for 可能。
- `runtime_protocol`: codegen は runtime の iterable プロトコル API を呼ぶ。

## 6. Runtime 契約（C++）

## 6.1 正規プロトコル

意味論上の正規 API は `iter/next` 形式にする。

- `py_iter_or_raise(obj) -> object`  
- `py_next_or_stop(iter_obj) -> optional<object>`

契約:

- iterable でない値の `py_iter_or_raise` は `TypeError` 相当を送出。
- `py_next_or_stop` は要素があれば `object`、終端なら `nullopt`。
- `__next__` 由来の `StopIteration` は `nullopt` へ正規化する。

`py_iter_or_raise` の解決順序:

1. まず `__iter__` を解決し、取得した iterator を返す。  
2. `__iter__` が無い場合はシーケンスフォールバックを試す（`__getitem__(0), __getitem__(1), ...` を `IndexError` まで）。  
3. どちらも不成立なら `TypeError` 相当を送出する。

## 6.2 C++ の begin/end ブリッジ

`for` 生成を C++ 側で自然に扱うため、`object/Any` 経路には begin/end ブリッジを用意する。

- `py_dyn_range(obj)` を導入し、`begin()` で `py_iter_or_raise`、`operator++` で `py_next_or_stop` を使う。
- 生成コードは `for (object v : py_dyn_range(x))` を使える。
- これは「begin/end で回す」表面 APIだが、意味論は `iter/next` に一致させる。

## 6.3 `PyObj` 拡張（推奨）

`PyObj` 側には少なくとも次を追加する。

- `virtual object py_iter_or_raise() const;`
- `virtual ::std::optional<object> py_next_or_stop();`

規約:

- 反復可能オブジェクトは `py_iter_or_raise` を override。
- iterator オブジェクトは `py_next_or_stop` を override。
- 未実装の既定は `TypeError` 相当（誤って空反復にしない）。

## 6.4 最適化ルール

- `list[T]` など静的型確定時は `for (T v : xs)` を生成し、`py_dyn_range` を経由しない。
- `object/Any/unknown union` は必ず `py_dyn_range`（または等価 while ループ）経由。
- これにより性能と互換性を両立する。

## 7. ディスパッチ方式切替（全ターゲット共通）

`type_id` の利用は機能ごとに分けず、単一オプションで一括切替する。

- `--object-dispatch-mode {type_id,native}`
- 既定値: `native`

モード定義:

- `type_id`:
  - `Any/object` 境界の dispatch を全面的に `type_id` で行う。
  - iterable では `py_iter_or_raise` / `py_next_or_stop` を `type_id` dispatch で解決する。
  - Boxing/Unboxing、`bool/len/str`、`iter/next` のすべてで同一方式を使う。
  - 名目的型判定（`isinstance` / `issubclass`）は `spec-type_id` の `py_is_subtype` / `py_isinstance` / `py_issubclass` 契約に従う。
- `native`:
  - `type_id` dispatch を一切使わない。
  - C++ は virtual/hook（必要時 dynamic cast）、JS/TS は `Symbol.iterator` / `next` などネイティブ機構で解決する。
  - `isinstance` / `issubclass` は target 固有機構で解決するが、`spec-type_id` と同じ観測結果を満たす。
  - `constructor.name` 依存 dispatch は禁止する。

禁止事項:

- 一部機能だけ `type_id`、他は `native` の混在（hybrid 運用）。

共通要件:

- C++ と同じ失敗契約（non-iterable は `TypeError` 相当）。
- 同一モードでは決定的挙動を維持する。
- `meta.dispatch_mode` はルートスキーマ入力をそのまま使い、backend/hook で再決定しない。
- dispatch mode の意味論適用点は `EAST2 -> EAST3` の lowering 1 回に限定する。

## 8. 変換器（py2cpp）規則

1. `ForRange` は既存どおり専用 fastpath を維持。  
2. 通常 `For` は EAST の `iter_mode` で分岐。  
3. `iter_mode=static_fastpath`:
- 直接 range-for を生成。
4. `iter_mode=runtime_protocol`:
- `for (object v : py_dyn_range(iter_expr))` を生成（または等価 while）。
5. ユーザー定義型で `__iter__` / `__next__` がある場合:
- class 生成時に runtime hook へ接続するコードを出力。

## 9. 段階導入

1. EAST に `iterable_trait` / `iter_mode` を追加。  
2. C++ runtime に `py_iter_or_raise` / `py_next_or_stop` / `py_dyn_range` を追加。  
3. `py2cpp` の `emit_for_each` を `iter_mode` 分岐へ移行。  
4. 共通 CLI に `--object-dispatch-mode`（`type_id` / `native`）を追加。  
5. 既存 fixture + 追加 tests で回帰を固定。

## 10. 受け入れ基準

- `object/Any` での `for` がユーザー定義 `__iter__` を経由して動作する。
- non-iterable に対する `for` が `TypeError` 相当で失敗する。
- `list` fastpath では `py_dyn_range` が生成されない。
- `--object-dispatch-mode=type_id` では iterable を含む `Any/object` 境界が全面的に type_id dispatch される。
- `--object-dispatch-mode=native` では iterable を含む `Any/object` 境界で type_id dispatch が一切生成されない。
- selfhost/transpile/build の既存導線に致命回帰を出さない。

## 11. テストコード例（5件）

以下は「この仕様が満たされていること」を確認する最小テスト例。

### 11.1 例1: `list` は static fastpath（codegen）

```python
import tempfile
import unittest
from pathlib import Path

from src.py2cpp import load_east, transpile_to_cpp


class IterableCodegenFastPathTest(unittest.TestCase):
    def test_for_list_uses_static_range_for(self) -> None:
        src = """def f() -> int:
    xs: list[int] = [1, 2, 3]
    s: int = 0
    for v in xs:
        s += v
    return s
"""
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "case.py"
            p.write_text(src, encoding="utf-8")
            cpp = transpile_to_cpp(load_east(p), emit_main=False)

        self.assertIn("for (int64 v : xs)", cpp)
        self.assertNotIn("py_dyn_range(xs)", cpp)
```

### 11.2 例2: `Any/object` は runtime iterable プロトコル（codegen）

```python
import tempfile
import unittest
from pathlib import Path

from src.py2cpp import load_east, transpile_to_cpp


class IterableCodegenDynamicTest(unittest.TestCase):
    def test_for_any_uses_runtime_protocol(self) -> None:
        src = """def f(x: object) -> int:
    s: int = 0
    for v in x:
        s += v
    return s
"""
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "case.py"
            p.write_text(src, encoding="utf-8")
            cpp = transpile_to_cpp(load_east(p), emit_main=False)

        self.assertIn("py_dyn_range(x)", cpp)
```

### 11.3 例3: ユーザー定義 `__iter__/__next__` が動作（fixture 実行）

```python
from pytra.utils.assertions import py_assert_stdout


class CounterIter:
    cur: int
    stop: int

    def __init__(self, stop: int):
        self.cur = 0
        self.stop = stop

    def __iter__(self):
        return self

    def __next__(self):
        if self.cur >= self.stop:
            raise StopIteration()
        out = self.cur
        self.cur += 1
        return out


class Counter:
    stop: int

    def __init__(self, stop: int):
        self.stop = stop

    def __iter__(self):
        return CounterIter(self.stop)


def main():
    s: int = 0
    for v in Counter(4):
        s += v
    print(s)


def _case_main() -> None:
    main()


if __name__ == "__main__":
    print(py_assert_stdout(["6"], _case_main))
```

### 11.4 例4: non-iterable では `TypeError` 相当（runtime）

```python
import tempfile
import unittest
from pathlib import Path

from src.py2cpp import load_east, transpile_to_cpp
from test.support.cpp_runner import build_and_run_cpp  # 既存fixture側helperを想定


class IterableTypeErrorTest(unittest.TestCase):
    def test_for_int_raises_not_iterable(self) -> None:
        src = """def main():
    x: object = 123
    for _v in x:
        print(_v)
"""
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "case.py"
            p.write_text(src, encoding="utf-8")
            cpp = transpile_to_cpp(load_east(p), emit_main=True)
            self.assertIn("py_dyn_range(x)", cpp)

            proc = build_and_run_cpp(cpp, workdir=Path(td))
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("TypeError", proc.stderr + proc.stdout)
```

### 11.5 例5: 単一モードでの一括切替（静的検査）

`transpile_js` と `SRC` は、JS/TS 向け既存fixtureの共通 helper で提供される前提。

```python
import unittest
from pathlib import Path


class JsTsIterableDispatchTest(unittest.TestCase):
    def test_object_dispatch_mode_switches_all_object_boundary_paths(self) -> None:
        js_typeid = transpile_js(SRC, object_dispatch_mode="type_id")
        js_native = transpile_js(SRC, object_dispatch_mode="native")

        # type_id モード: iterable/bool/len/boxing の全経路で type_id を使う。
        self.assertIn("type_id", js_typeid)
        self.assertIn("py_iter_or_raise_typeid", js_typeid)
        self.assertIn("py_len_typeid", js_typeid)
        self.assertIn("make_object_typeid", js_typeid)

        # native モード: type_id 経路が 1 つも残らない。
        self.assertNotIn("type_id", js_native)
        self.assertNotIn("_typeid", js_native)
        self.assertIn("Symbol.iterator", js_native)
```

## 12. メモ

- C++ では begin/end ブリッジを採用しても、意味論の正本は `iter/next` とする。  
- これにより、Python と非 C++ ターゲットに同じ仕様を展開しやすくなる。  
- 既存 `spec-boxing.md` の fail-fast 方針（暗黙空反復禁止）と整合する。

## 13. 関連

- `docs-ja/spec/spec-east.md`
- `docs-ja/spec/spec-linker.md`
- `docs-ja/spec/spec-type_id.md`
- `docs-ja/spec/spec-boxing.md`
- `docs-ja/spec/spec-dev.md`
