# P6: list.clear() / dict.clear() を C++ emitter でサポートする

最終更新: 2026-03-18

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P6-CPP-EMIT-LIST-DICT-CLEAR-01`

## 背景

`src/pytra/built_in/type_id.py` は `dict[int64, ...]` および `list[int64]` に対して `.clear()` を
呼び出している。現在の C++ emitter はこれを BuiltinCall として lowering しておらず、
transpilation に失敗する：

```
error: internal error occurred during transpilation.
detail: builtin method call must be lowered_kind=BuiltinCall: list[int64].clear
```

このため `type_id.py` を transpiler で再生成できず、`generated/built_in/type_id.cpp` を
手動編集しなければならない状態になっている。`generated/` の手動編集は禁止されているため、
これを解除することが本タスクの目的である。

### 対応するファイル

| Python ソース | 問題の箇所 | 影響する生成ファイル |
|---|---|---|
| `src/pytra/built_in/type_id.py` | `_TYPE_ORDER.clear()` 等（dict/list の .clear()） | `generated/built_in/type_id.cpp` |

### C++ 変換

- `list<T>.clear()` → `v.clear()`
- `dict<K, V>.clear()` → `v.clear()`
- `rc<list<T>>.clear()` → `rc_list_ref(v).clear()`

いずれも標準 C++ コンテナの `.clear()` メソッドに直接マッピングできる。

## 目的

- C++ emitter が `list.clear()` / `dict.clear()` を BuiltinCall として lowering し、
  `v.clear()` を emit できるようにする。
- `type_id.py` を transpiler で再生成できるようにする。
- `generated/built_in/type_id.cpp` を再生成で最新化する。

## 対象

- `src/toolchain/emit/cpp/emitter/`（BuiltinCall lowering の追加）
- EAST3 IR の BuiltinCall ノード定義（必要に応じて）
- `src/runtime/cpp/generated/built_in/type_id.cpp`（再生成）

## 非対象

- `set.clear()` / `deque.clear()` など他コンテナへの対応（本タスクでは list/dict に限定、
  必要に応じて後続タスクで拡張）
- 非 C++ バックエンドへの対応

## 受け入れ基準

- `PYTHONPATH=src python3 src/toolchain/emit/cpp/cli.py src/pytra/built_in/type_id.py` が成功する。
- 再生成した `type_id.cpp` でコンパイルが通る。
- selfhost diff mismatches=0。

## 決定ログ

- 2026-03-18: `generated/` 手動編集禁止ルールの下で P6-EAST3-IS-NONE-INLINE-01 を実施するために必要なブロッカーとして特定。`.clear()` は C++ 標準コンテナに直接対応する最も単純なケース。
