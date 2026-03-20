# P0: tagged union の型ナローイングを cast() 方式に統一

最終更新: 2026-03-18

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-TAGGED-UNION-CAST-NARROWING-01`

## 背景

tagged union 変数から特定の型の値を取り出す際、現在は isinstance ガード内の
暗黙ナローイング（emitter がスコープを追跡してフィールドアクセスに自動変換）で実装している。

この方式には以下の問題がある：

1. **型変換の意図がソースコードに現れない** — isinstance を書いても、代入・使用時に型が確定していることが明示されない
2. **emitter のスコープ追跡が fragile** — 属性アクセス（`s.default`）やネストした条件には対応困難
3. **isinstance ガードなしの代入が暗黙的に通る** — `values[s.dest] = s.default` は ArgValue → ArgValue の代入で動くが、本来は型を確定させるべき

## 修正方針

`typing.cast(T, v)` を tagged union のフィールドアクセスに変換する。

### Python 側

```python
from typing import cast

if isinstance(v, int):
    x: int = cast(int, v)       # v の int フィールドを取り出す
    print(x + 1)

if isinstance(s.default, bool):
    values[s.dest] = cast(bool, s.default)  # s.default の bool フィールドを取り出す
```

### C++ 生成

```cpp
if ((v).tag == PYTRA_TID_INT) {
    int64 x = v.int64_val;
    py_print(x + 1);
}

if ((s.py_default).tag == PYTRA_TID_BOOL) {
    values[s.dest] = s.py_default.bool_val;
}
```

### 実装ステップ

1. emitter で `cast(T, v)` を検出し、`v` が tagged union 型の場合に `v.{T_field}` に変換するロジックを追加
2. isinstance ガードによる暗黙ナローイング（`_narrowed_union_vars`）を除去
3. `argparse.py` を `cast()` 方式に書き換え
4. 仕様を `docs/ja/spec/spec-tagged-union.md` に記載（済み）
5. テスト更新

## 対象

- `src/toolchain/emit/cpp/emitter/cpp_emitter.py` — cast 検出・tagged union フィールドアクセス変換
- `src/toolchain/emit/cpp/emitter/stmt.py` — 暗黙ナローイング除去
- `src/toolchain/emit/cpp/emitter/call.py` or `builtin_runtime.py` — cast BuiltinCall の処理
- `src/pytra/std/argparse.py` — cast() 方式へ書き換え

## 非対象

- 非 C++ バックエンド
- Generic cast（`cast(list[int], v)` 等の複合型への cast）— まずはプリミティブ型のみ

## 受け入れ基準

- `cast(bool, v)` が tagged union 変数に対して `v.bool_val` を生成する。
- isinstance ガードによる暗黙ナローイングが除去されている。
- `argparse.py` が `cast()` を使用する形に修正されている。
- fixture / sample pass。

## 決定ログ

- 2026-03-18: ユーザー指摘。isinstance ガードだけでは型が確定しない。`cast()` で明示的に型を確定させるべき。
  `typing.cast` は Python 実行時 no-op なので互換性に影響なし。仕様 `spec-tagged-union.md` に記載。
- 2026-03-18: 実装完了。`_try_render_tagged_union_cast` を call.py に追加。`cast(T, v)` を `v.{T_field}` に変換。
  暗黙ナローイング（`_narrowed_union_vars`、`_detect_isinstance_narrowing`、`_render_name_expr` の narrowing パス）を除去。
  argparse.py を `cast(bool, dv)` 方式に修正。242 test pass。
