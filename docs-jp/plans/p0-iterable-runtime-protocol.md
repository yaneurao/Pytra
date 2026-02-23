# P0 Iterable/Iterator 契約反映（最優先）

ID: `TG-P0-ITER`

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

## 実施項目

1. `docs-jp/spec/spec-iterable.md` を正本として固定し、仕様と TODO を同期する。
2. `EAST` に iterable trait と `For.iter_mode` を導入し、codegen 分岐を明示化する。
3. C++ runtime に `py_iter_or_raise` / `py_next_or_stop` / `py_dyn_range` を導入する。
4. `py2cpp` で `static_fastpath` と `runtime_protocol` を明示分岐する。
5. `--object-dispatch-mode {type_id,native}` の iterable 境界要件を cross-target で固定する。

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
