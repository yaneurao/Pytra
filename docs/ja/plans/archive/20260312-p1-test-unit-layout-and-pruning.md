<a href="../../../en/plans/archive/20260312-p1-test-unit-layout-and-pruning.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P1: `test/unit` レイアウト再編と未使用テスト整理

最終更新: 2026-03-04

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-TEST-UNIT-LAYOUT-PRUNE-01`

背景:
- `test/unit/` に言語別・IR・tooling・selfhost関連テストが混在しており、探索性と保守性が低下している。
- `test_py2*_smoke.py` のような backend 系テストと、`test_east*` / `test_code_emitter.py` のような共通層テストが同一階層に並び、責務境界が読み取りづらい。
- 過去の移行で残置されたテストの中に、現行運用で参照されない（discover対象外・個別実行導線なし）候補がある。

目的:
- `test/unit` を責務別ディレクトリへ再編し、テスト探索コストを下げる。
- 「未使用テスト候補」を機械的に棚卸しし、削除/統合/維持を根拠付きで決定する。
- 再編後も既存の unit/transpile/selfhost 回帰導線を維持する。

対象:
- `test/unit/` 配下の再配置（例: `common`, `backends/<lang>`, `ir`, `tooling`, `selfhost`）
- `tools/` / `docs/` の test path 参照更新
- 未使用候補テストの判定・整理（削除または統合）
- 再流入防止の検査追加（任意）

非対象:
- backend 生成品質の改善
- fixture の意味変更
- parity test 仕様変更

受け入れ基準:
- `test/unit` が責務別フォルダ構成へ再編され、トップレベル直下の混在が解消される。
- 主要実行導線（`unittest discover`, `tools/check_py2*_transpile.py`, selfhost check）が新パスで通る。
- 未使用テスト整理について「削除/統合/維持」の判断根拠（参照有無・実行実績）を残す。
- 誤削除防止のため、削除対象は少なくとも 1 回の全体 discover と参照スキャンで未使用確認を満たす。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 -m unittest discover -s test/unit -p 'test*.py'`
- `rg -n \"test/unit/|test_py2.*smoke\" tools docs/ja docs/en -g '*.py' -g '*.md'`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/check_py2rs_transpile.py`
- `python3 tools/check_py2cs_transpile.py`
- `python3 tools/check_py2js_transpile.py`
- `python3 tools/check_py2ts_transpile.py`
- `python3 tools/check_py2go_transpile.py`
- `python3 tools/check_py2java_transpile.py`
- `python3 tools/check_py2swift_transpile.py`
- `python3 tools/check_py2kotlin_transpile.py`
- `python3 tools/check_py2rb_transpile.py`
- `python3 tools/check_py2lua_transpile.py`
- `python3 tools/check_py2scala_transpile.py`
- `python3 tools/check_py2php_transpile.py`
- `python3 tools/check_py2nim_transpile.py`

## 分解

- [x] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S1-01] `test/unit` の現行テストを責務分類（common/backends/ir/tooling/selfhost）で棚卸しし、移動マップを確定する。
- [x] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S1-02] 目標ディレクトリ規約を定義し、命名・配置ルールを決定する。
- [x] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S2-01] テストファイルを新ディレクトリへ移動し、`tools/` / `docs/` の参照パスを一括更新する。
- [x] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S2-02] `unittest discover` と個別実行導線が新構成で通るように CI/ローカルスクリプトを更新する。
- [x] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S3-01] 未使用テスト候補を抽出し、`削除/統合/維持` を判定する監査メモを作成する。
- [x] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S3-02] 判定済みの未使用テストを削除または統合し、再発防止チェック（必要なら新規）を追加する。
- [x] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S4-01] 主要 unit/transpile/selfhost 回帰を実行し、再編・整理後の非退行を確認する。
- [x] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S4-02] `docs/ja/spec`（必要なら `docs/en/spec`）へ新しいテスト配置規約と運用手順を反映する。

決定ログ:
- 2026-03-04: ユーザー指示により、`test/unit` の責務別フォルダ再編と未使用テスト整理を P1 タスクとして起票した。削除は必ず監査根拠付きで段階実施する方針を採用。
- 2026-03-04: `S1-01` を完了。`test/unit` 71本を責務分類し、移動マップを確定した。分類結果は `backends/*:29, ir:10, tooling:5, selfhost:3, common:23`。`S2-01` ではこのマップに従ってディレクトリ再編を実施する。
- 2026-03-04: `S1-02` を完了。`test/unit` の目標配置規約を `責務ディレクトリ + 命名規約 + discover/実行規約 + 追加時チェック` で固定し、`S2` 以降の移動判断基準を確定した。
- 2026-03-04: `S2-01` を完了。`test/unit/test_*.py` 71本を `common/backends/<lang>/ir/tooling/selfhost` へ `git mv` し、`tools/run_local_ci.py` と `tools/check_noncpp_east3_contract.py` の固定テストパスを新配置へ更新した。`test/unit/backends` を package 化すると `src/backends` と名前衝突するため、`__init__.py` は置かない方針を採用（discover 導線は `S2-02` で更新）。
- 2026-03-04: `S2-02` を完了。`test/unit/test_discovery_router.py` を `load_tests + importlib` の手動ローダに差し替え、非package配下でも `python3 -m unittest discover -s test/unit -p 'test*.py'` が再帰実行できるようにした。個別実行で壊れていた `from comment_fidelity import ...` はルート `comment_fidelity.py` 追加で安定化し、`go/swift/kotlin` smoke discover 3本の通過を確認した。`tools/check_gsk_native_regression.py` も新パス（`test/unit/backends/*`）参照へ更新済み。
- 2026-03-04: `S3-01` を完了。`test/unit/test*.py` 全件に対して `tools/docs` 参照スキャンを実施し、参照ゼロ候補（`test_pylib_*`, `test_east3_to_human_repr.py`）を抽出。候補はすべて discover 配下の現役回帰（`python3 -m unittest discover -s test/unit/common -p 'test_pylib_*.py'`, `... -s test/unit/ir -p 'test_east3_to_human_repr.py'` 通過）と判定し、削除・統合は見送り（維持）とした。
- 2026-03-04: `S3-02` を完了。`S3-01` の監査結論（削除/統合候補 0 件）に基づき、コード変更なしでクローズ。再発防止は `test/unit` 直下直置き禁止規約と `test_discovery_router` の固定により担保する。
- 2026-03-04: `S4-01` を完了。主要回帰として `test/unit/common/test_py2x_smoke_common.py`, `test/unit/backends/{go,swift,kotlin}/test_py2*_smoke.py`, `test/unit/selfhost/test_prepare_selfhost_source.py`, `tools/check_noncpp_east3_contract.py --skip-transpile` を再実行し全通過を確認した。
- 2026-03-04: `S4-02` を完了。`docs/ja/spec` / `docs/en/spec` のテストパス参照（`test/unit/test_*.py`）を新配置へ更新し、`common/backends/ir/tooling/selfhost` 運用へ揃えた。

## S3-01 監査メモ（2026-03-04）

- 抽出手順:
- `test/unit/test*.py` を全列挙し、各 `basename` について `rg -n <basename> tools docs/ja docs/en` のヒット件数を集計。
- ヒット 0〜1 件を「未使用候補」として抽出し、discover 実行有無で再判定。
- 候補と判定:
- `test/unit/common/test_pylib_argparse.py` ほか `test_pylib_*` 8本:
- 判定 `維持`。`test/unit/common` discover で 36 tests pass。`src/pytra/*` の shim 回帰を担うため削除不可。
- `test/unit/ir/test_east3_to_human_repr.py`:
- 判定 `維持`。`test/unit/ir` 個別 discover で 3 tests pass。`east2/east3` human repr の互換ラッパ契約を担保。
- `test/unit/test_discovery_router.py`:
- 判定 `維持`。`test/unit/backends` 非package運用時の top-level discover ルータとして必須。
- 監査結論:
- 今回の `S3-01` では「削除/統合」対象は 0 件。`S3-02` は `候補なしでクローズ` とする。

## S1-01 棚卸し結果（2026-03-04）

- 総数: `test/unit/test*.py` 71本
- 分類サマリ:
- `backends/*`: 29本
- `ir`: 10本
- `tooling`: 5本
- `selfhost`: 3本
- `common`: 23本
- 目標移動先（確定）:
- `test/unit/backends/<lang>/`: `test_py2<lang>_smoke.py` 系 + backend固有テスト
- `test/unit/ir/`: `test_east*.py` 系
- `test/unit/tooling/`: CLI/manifest/parity tool テスト
- `test/unit/selfhost/`: selfhost build/diff/regression テスト
- `test/unit/common/`: 上記以外の cross-lang / pylib / profile / bootstrap テスト
- 主要マップ（明示分）:
- `backends/cpp`:
- `test_check_microgpt_original_py2cpp_regression.py`, `test_cpp_*.py`, `test_py2cpp_*.py`, `test_east3_cpp_bridge.py`, `test_noncpp_east3_contract_guard.py`
- 各言語 backend:
- `test_py2{rs,cs,js,ts,go,java,swift,kotlin,rb,lua,php,nim}_smoke.py`, `test_check_py2scala_transpile.py`, `test_py2scala_smoke.py`
- `ir`:
- `test_east1_build.py`, `test_east2_to_east3_lowering.py`, `test_east3_*.py`, `test_east_core.py`, `test_east_stage_boundary_guard.py`
- `tooling`:
- `test_docs_ja_guard.py`, `test_gen_makefile_from_manifest.py`, `test_ir2lang_cli.py`, `test_pytra_cli.py`, `test_runtime_parity_check_cli.py`
- `selfhost`:
- `test_check_selfhost_cpp_diff.py`, `test_prepare_selfhost_source.py`, `test_selfhost_virtual_dispatch_regression.py`
- `common`:
- 上記以外の 23 本（`test_code_emitter.py`, `test_py2x_smoke_common.py`, `test_pylib_*.py`, `test_language_profile.py` など）

## S1-02 目標ディレクトリ規約（2026-03-04）

- ルート構成:
- `test/unit/common/`: 言語横断の共通テスト（IR非依存・backend非依存）
- `test/unit/backends/<lang>/`: 言語 backend 固有テスト（`<lang>` は `cpp,rs,cs,js,ts,go,java,swift,kotlin,rb,lua,scala,php,nim`）
- `test/unit/ir/`: EAST1/2/3・最適化・境界契約の IR テスト
- `test/unit/tooling/`: CLI / parity / manifest / docs-guard など運用系テスト
- `test/unit/selfhost/`: selfhost 生成・差分・退行テスト
- ファイル命名:
- ファイル名は `test_*.py` を維持し、移動で `basename` は原則変更しない（履歴追跡と既存参照維持のため）。
- backend 固有新規テストは `test_<lang>_*.py` または `test_py2<lang>_*.py` を優先し、`common` との識別を容易にする。
- 実行規約:
- 全体実行の基準は `python3 -m unittest discover -s test/unit -p 'test*.py'` を維持する。
- 個別実行は `python3 -m unittest discover -s test/unit/<domain> -p 'test*.py'` で domain 単位に可能とする。
- 参照更新規約:
- `tools/` / `docs/` が旧パスを参照している場合は、`S2-01` で必ず新パスへ同一コミットで更新する。
- 追加時チェック:
- 新規テスト追加時は `common/backends/ir/tooling/selfhost` のいずれかへ必ず分類し、`test/unit` 直下への直置きは不可とする。
