# P0 Iterable/Iterator 契約反映（最優先）

ID: `TG-P0-ITER`

## 関連 TODO

- `docs-jp/todo.md` の `ID: P0-ITER-01`（`P0-ITER-01-S1` 〜 `P0-ITER-01-S4`）

## 背景

- `materials/refs/spec-iterable.md` に、`for ... in ...` の動作を Python の `iter/next` 契約へ寄せる改良案を整理した。
- 現状は `object/Any` 境界で反復契約が不安定で、ユーザー定義 `__iter__/__next__` と non-iterable 失敗契約が十分に固定されていない。
- この領域は `spec-boxing` の境界契約とも強く連動するため、優先して仕様固定と実装計画化が必要。

## 目的

- `docs-jp/spec/spec-iterable.md` を実装時の正本仕様として扱う。
- `EAST` の `iter_mode` / `iterable_trait` と runtime の `py_iter_or_raise` / `py_next_or_stop` を一貫した契約で導入する。
- `list` 系の静的 fastpath と `object/Any` の動的 protocol を両立する。

## 非対象

- `async for` / `__aiter__` / `__anext__` 対応。
- 例外メッセージ文言の CPython 完全一致。
- 性能最適化のみを目的とした先行変更。

## サブタスク実行順（todo 同期）

1. `P0-ITER-01-S1`: `EAST` trait（`iterable_trait` / `iter_mode`）で必要なメタデータを確定し、影響ノードを整理する。
2. `P0-ITER-01-S2`: parser/lower から `EAST` trait を供給できるようにし、既存 `For` への互換移行を固定する。
3. `P0-ITER-01-S3`: C++ runtime に `py_iter_or_raise` / `py_next_or_stop` / `py_dyn_range` を実装し、non-iterable fail-fast 契約を固定する。
4. `P0-ITER-01-S4`: `py2cpp` の `static_fastpath` / `runtime_protocol` 分岐と回帰テストを整備する。

## 受け入れ基準

- `object/Any` の `for` が `__iter__` / `__next__` を経由して動作する。
- non-iterable の `for` が `TypeError` 相当で失敗する。
- `list` fastpath では `py_dyn_range` が生成されない。
- 同一入力で mode ごとの dispatch 方式が決定的に切り替わる。

## 決定ログ

- 2026-02-23: `materials/refs/spec-iterable.md` を `docs-jp/spec/spec-iterable.md` へコピーし、`P0-ITER-01` を TODO 最優先に追加。
- 2026-02-23: Phase 1 として C++ runtime に `PyObj::py_iter_or_raise` / `PyObj::py_next_or_stop` と `py_iter_or_raise(...)` / `py_next_or_stop(...)` / `py_dyn_range(...)` を導入し、`PyListObj` / `PyDictObj` / `PyStrObj` は iterator object を返す実装へ更新した。non-iterable は `TypeError` 相当（`runtime_error`）で fail-fast とする。
- 2026-02-23: `py2cpp` の `For` 生成は `iter_mode`（`static_fastpath` / `runtime_protocol`）で分岐する。`runtime_protocol` は `for (object ... : py_dyn_range(iterable))` を生成し、tuple unpack は `py_at(...)` で展開する。
- 2026-02-23: selfhost 安定性のため、`iter_mode` 未付与の既存 EAST は `unknown` を既定 `static_fastpath` として扱う（互換優先）。`object/Any` は parser 側で明示 `runtime_protocol` を付与して切り替える。
- 2026-02-23: C++ runtime の object iterable 経路で `set` を扱えるようにした。`PySetObj`（`PYTRA_TID_SET`）と `make_object(const set<T>&)` を追加し、`py_dyn_range(make_object(set<...>))` が反復可能であること、`py_isinstance(make_object(set<...>), PYTRA_TID_SET)` が成立することを `test/unit/test_cpp_runtime_iterable.py` / `test/unit/test_cpp_runtime_type_id.py` で固定した。
- 2026-02-23: docs-jp/todo.md の P0-ITER-01 を -S1 〜 -S4 へ分割したため、本 plan 側にも同粒度の実行順を追記した。
