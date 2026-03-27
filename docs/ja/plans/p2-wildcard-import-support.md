<a href="../../en/plans/p2-wildcard-import-support.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P2: `from ... import *`（ワイルドカード import）正式対応

最終更新: 2026-03-02

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P2-WILDCARD-IMPORT-01`

背景:
- 現状の self-hosted parser は `from M import *` を受理して `binding_kind=wildcard` を保持するが、解決・展開が未実装のため、生成コードで未定義シンボルが残る。
- CLI の既存回帰テストには「`from M import *` は `input_invalid`」期待が残っており、実装とテストの契約が不整合になっている。
- ドキュメント上でも wildcard import の扱いが揺れており、仕様・実装・テストを同じ契約へ揃える必要がある。

目的:
- `from M import *` を multi-file 変換で一貫して解決し、通常の `from M import name` と同様に backend へ安全に受け渡す。
- 解決不能ケース（公開シンボルを静的確定できない等）は fail-closed で `input_invalid` を返し、不正な生成コードを出さない。

対象:
- import graph / export table への wildcard 展開ルール追加
- `meta.import_bindings` / `import_symbols` 構築時の wildcard 束縛解決
- CLI エラーハンドリング（unsupported から解決失敗系エラーへ契約更新）
- wildcard import 回帰テスト（unit + multi-file transpile）
- 仕様ドキュメント（`spec-user.md` / `spec-import.md`）の整合

非対象:
- 相対 import（`from .m import x`）のサポート
- 動的 import（`__import__`）や runtime 依存の遅延解決
- wildcard import に起因しない通常 import 最適化

受け入れ基準:
- `from helper import *` を含む multi-file 入力で、公開シンボル参照が正しく解決されること。
- 同名シンボル衝突（例: `from a import *` + `from b import *`）は fail-closed で `input_invalid(kind=duplicate_binding)` になること。
- 解決不能な wildcard（公開シンボルを静的確定できない場合）は `input_invalid` で停止し、未定義参照の生成コードを出力しないこと。
- 既存 import 回帰（missing module / cycle / relative import）を壊さないこと。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_features.py' -v`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/check_py2rs_transpile.py`

決定ログ:
- 2026-03-01: ユーザー指示により、`from ... import *` を「拒否」ではなく「正式対応 + 解決不能は fail-closed」方針で `P2` 起票した。
- 2026-03-02: `validate_from_import_symbols_or_raise` で wildcard 解決を実装し、`__all__` が静的に確定できない場合は `kind=unresolved_wildcard` で fail-closed する契約へ統一した。
- 2026-03-02: wildcard 展開結果を `meta.import_symbols` / `meta.qualified_symbol_refs` / `meta.import_resolution.qualified_refs` へ反映し、backend 参照解決を既存経路で利用可能にした。
- 2026-03-02: `test_py2cpp_features` に wildcard 正常系/重複/未解決の unit+CLI 回帰を追加し、`discover -k validate_from_import_symbols_or_raise` と `discover -k from_import_star` を通過した。
- 2026-03-02: `docs/ja/spec/spec-import.md` と `docs/en/spec/spec-import.md` / `docs/en/spec/spec-user.md` を更新し、`from ... import *` の正式対応と `unresolved_wildcard` 契約を明文化した。

## 分解

- [x] [ID: P2-WILDCARD-IMPORT-01-S1-01] wildcard import の公開シンボル決定規則（`__all__` 優先、未定義時は public 名）を仕様化する。
- [x] [ID: P2-WILDCARD-IMPORT-01-S1-02] 既存 import 診断契約（unsupported/duplicate/missing）のどれに寄せるかを整理し、エラー分類を固定する。
- [x] [ID: P2-WILDCARD-IMPORT-01-S2-01] import graph / export table で wildcard 展開情報を構築し、`meta.import_bindings` と解決テーブルへ反映する。
- [x] [ID: P2-WILDCARD-IMPORT-01-S2-02] 同名衝突・非公開名・未解決 wildcard を fail-closed で検出し、`input_invalid` を返す。
- [x] [ID: P2-WILDCARD-IMPORT-01-S2-03] CLI の wildcard 例外分岐と回帰テスト期待値を「正式対応」契約に更新する。
- [x] [ID: P2-WILDCARD-IMPORT-01-S3-01] unit/統合テスト（`from helper import *` 正常系 + 衝突/失敗系）を追加して再発検知を固定する。
- [x] [ID: P2-WILDCARD-IMPORT-01-S3-02] `spec-user.md` / `spec-import.md` / TODO の記述を実装契約に同期する。
