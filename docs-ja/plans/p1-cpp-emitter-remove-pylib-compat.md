# P1: CppEmitter の pylib 互換名正規化除去

最終更新: 2026-02-25

## 目的

`src/hooks/cpp/emitter/cpp_emitter.py` にある `_normalize_runtime_module_name` を削除し、`pylib.*` 互換の強制変換を廃止して
`cpp_emitter.py` の名前解決を `pytra.*` 系統のみで完結させる。

## 背景

- `cpp_emitter.py` の命名正規化は、旧 `pylib` 系と `pytra` 系の共存運用に対する互換措置として存在している。
- これ以上旧互換を維持しない方針のため、重複分岐を残したままにすると保守コストと解析分岐が残る。
- `src/pytra/compiler/east_parts/code_emitter.py` 側にも同名ロジックに相当する箇所があり、全体としての整合整理が必要。

## 非対象

- `pylib.*` を新規サポートする実装追加
- `py2cpp.py` 本体の大規模再設計（既存移行タスクとして別管理）
- Pythonランタイム API の仕様変更

## 受け入れ条件

- `src/hooks/cpp/emitter/cpp_emitter.py` と `src/hooks/cpp/emitter/call.py` から `_normalize_runtime_module_name` への依存を削除する。
- `pylib.*` 名の入力を前提とした変換経路を廃止する（互換を持たないことをドキュメントで明示）。
- テスト（少なくとも `tools/check_py2cpp_transpile.py` または `test/unit/test_py2cpp_*.py`）で、`pylib` 前提ケースが新規に必要でないことを確認する。

## 作業順（推奨）

### `P1-CPP-EMIT-NORM-01-S1`
- `src/hooks/cpp/emitter/cpp_emitter.py` の `_normalize_runtime_module_name` 呼び出し箇所を洗い出し、直結除去の影響範囲を確定。
- 置換方針（`module_namespace_map`/`dict_any_get_str`/`module_name` 参照）の実装方針を決定。

### `P1-CPP-EMIT-NORM-01-S2`
- `src/hooks/cpp/emitter/cpp_emitter.py` および `src/hooks/cpp/emitter/call.py` のコードを `pylib` 正規化抜きで更新。
- 不要なヘルパメソッド本体を削除または `src/pytra/compiler/east_parts/code_emitter.py` 側の移行可否と整合。

### `P1-CPP-EMIT-NORM-01-S3`
- テストと検証を更新。
- 旧互換前提の fixture が残る場合は該当を非対象化し、代替検証（既存回帰）へ置換。

## 受け入れログ

- [x] 2026-02-25: `P1-CPP-EMIT-NORM-01-S1` 実施。`cpp_emitter.py` と `call.py` のすべての `_normalize_runtime_module_name` 呼び出しを廃止し、`pylib.*` 互換正規化を経路から除外した。
- [x] 2026-02-25: `P1-CPP-EMIT-NORM-01-S2` 実施。`src/pytra/compiler/east_parts/code_emitter.py` の既定 `_normalize_runtime_module_name` は恒等実装であり、`pylib.*` 前提の変換分岐は存在せず追加変更なし。

- [ ] 実施中: `pylib.*` 互換名正規化除去タスク（S2, S3）
