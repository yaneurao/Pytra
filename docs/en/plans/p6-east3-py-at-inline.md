<a href="../../ja/plans/p6-east3-py-at-inline.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/p6-east3-py-at-inline.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/p6-east3-py-at-inline.md`

# P6: py_at（list/rc 版）を EAST3 IR 経由インライン emit に移行し py_runtime.h から除去

最終更新: 2026-03-18

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P6-EAST3-PY-AT-INLINE-01`

## 背景

`py_at(v, idx)` は `py_runtime.h` に list / rc<list> / dict の 5 overload で定義されており、C++ emitter がインデックスアクセスを文字列として直接 emit している。

- `list<T>` 版 → `py_list_at_ref(v, idx)` に委譲しているだけであり、既存の `list_ops.h` を直接 emit すれば py_at を経由する必要がない。
- `rc<list<T>>` 版 → `py_list_at_ref(rc_list_ref(v), idx)` に展開可能。
- `dict<K, V>` 版 → キー型変換ロジックを含むため、list 版より複雑。dict 版の扱いは着手時に検討する。

`py_len` / `py_slice` の除去（P6-EAST3-LEN-SLICE-NODE-01）と同様のアプローチで、list/rc 版の `py_at` を emitter 側でインライン展開し、`py_runtime.h` から除去する。

## 目的

- `py_at`（list / rc<list> 版）の emit を `py_list_at_ref` 直接 emit に統一する。
- list/rc 版の `py_at` を `py_runtime.h` から削除する。
- dict 版は複雑さを確認の上、本タスクに含めるか後続タスクとするか着手時に決定する。

## 対象

- `src/toolchain/emit/cpp/emitter/`（`py_at` emit 箇所）
- `src/runtime/cpp/native/core/py_runtime.h`（除去対象関数）
- `tools/unittest/emit/cpp/`（回帰テスト）

## 非対象

- 非 C++ バックエンドへの対応
- `py_index` / `py_at_bounds` / `py_at_bounds_debug`（別途検討）

## 受け入れ基準

- 生成 C++ に `py_at(list_or_rc, idx)` の呼び出しが残らない（生成コード内）。
- list/rc 版の `py_at` が `py_runtime.h` から削除されている。
- fixture 3/3・sample 18/18 pass、selfhost diff mismatches=0。

## 決定ログ

- 2026-03-18: py_list_at_ref への委譲のみの list/rc 版は除去コストが低い。dict 版はキー型変換ロジックを含むため優先度を下げて別途判断。起票。
- 2026-03-18: 実装完了。list/rc<list> 版の py_at を py_runtime.h から除去。emitter が py_list_at_ref を直接 emit するよう変更（_render_sequence_index, subscript emit）。dict/tuple/object 境界の py_at は維持。241 test pass。
