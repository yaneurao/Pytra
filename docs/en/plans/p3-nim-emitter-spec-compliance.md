<a href="../../ja/plans/p3-nim-emitter-spec-compliance.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/p3-nim-emitter-spec-compliance.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/p3-nim-emitter-spec-compliance.md`

# P3: Nim emitter spec-emitter-guide 準拠改善

最終更新: 2026-03-23

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P3-NIM-SPEC-*`

背景:
- Nim emitter は spec-emitter-guide の主要条項（§1-§9, §12）に準拠済みだが、§7/§10/§11/§13 に未対応項目が残る。
- 2026-03-23 の改修で @extern 委譲コード生成、import パス機械的導出、is_entry ガード、ForRange 対応等を実施。
- 残存違反は「動作に影響しないが仕様準拠としては不完全」なものであり、P3 で計画的に対応する。

非対象:
- 既存 EAST3 型推論の不足（`seq[auto]` 問題等）は EAST3 パイプライン側の課題であり、emitter 改修では対処しない。
- work/transpile/nim/ の旧構造ファイルの移行は別タスク。

受け入れ基準:
- 全 4 項目の対応が完了し、§14 チェックリストの全項目が ✅ になる。

## S1: `build_import_alias_map` の利用（§7）

現状: import alias 解決に `_collect_relative_import_name_aliases` という独自実装を使用。
目標: 共通ユーティリティ `build_import_alias_map(meta)` を使用する。
影響: import alias のある sample が正しく解決されること。

## S2: コンテナ参照セマンティクス（§10）

現状: Nim の `seq[T]` / `Table[K,V]` を値型のまま使用。`var` 引数で変異パラメータを回避。
目標: `ref seq[T]` 等の参照型ラッパーを導入し、§10.5 の `container_value_locals_v1` ヒントで値型縮退を許可する。
影響: コンテナを引数に渡して変異する sample が正しく動作すること。

注意:
- 現行 18 sample は全てローカルコンテナまたは `var` パラメータで動作するため、実害は発生していない。
- 参照ラッパー導入は runtime 変更を伴う大規模リファクタリング。

## S3: `yields_dynamic` 対応（§11）

現状: `yields_dynamic: true` の明示処理がない。
目標: Call ノードの `yields_dynamic` フラグを確認し、必要に応じて型変換を生成する。
影響: Nim は generic `Table[K,V]` を使用するため `getOrDefault` は正しい型を返す。実害なし。ただし spec 準拠のためフラグの存在を確認するコードを追加する。

## S4: `runtime_parity_check.py` Nim toolchain 登録（§13）

現状: `runtime_parity_check.py --targets nim` で `missing toolchain` となり SKIP。
目標: Nim のコンパイル・実行パイプラインを `runtime_parity_check.py` に登録し、全 18 sample が PASS する。
影響: CI/CD での自動検証が可能になる。

備考:
- Nim ではモジュール名が数字で始められないため、エントリファイルに `m_` prefix が必要。
- `--path:.` コンパイルフラグが必要（`std/math` のローカル優先解決）。

## 決定ログ

- 2026-03-23: spec-emitter-guide §1-§13 の全条項を Nim emitter に照合。§1/§2/§3/§4/§5.1/§6/§8/§9/§12 を修正済み。残存 4 項目を P3 で起票。
