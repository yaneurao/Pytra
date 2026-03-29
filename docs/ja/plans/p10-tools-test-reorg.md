# P10-REORG: tools/ と tools/unittest/ の棚卸し・統合・管理台帳

最終更新: 2026-03-28
ステータス: 未着手

## 背景

tools/ と tools/unittest/ に agent が勝手にファイルを追加し、管理台帳がないため把握できなくなっている。

- tools/ にはスクリプトが 36 個あり、不要なものや用途不明なものが混在
- tools/unittest/ のサブフォルダ（backends, common, compile, ir, link, selfhost, toolchain2, tooling）の責務がどこにも定義されていない
- agent が AGENTS.md を読まずにファイルを追加するため、ルールでは防げない

## 設計方針

### tools/ のフォルダ分け

tools/ 直下にファイルを置くことを禁止し、サブディレクトリに分類する。

```
tools/
  check/    — CI チェック・検証（check_*.py, runtime_parity_check.py 等）
  gen/      — コード生成・golden 生成・sample 再生成（generate_*.py, regenerate_*.py 等）
  run/      — 一括実行（run_local_ci.py, run_regen_on_version_bump.py）
  unittest/ — 単体テスト（tools/unittest/ から移動）
```

tools/ 直下に置かれたファイルは管理外として即削除対象とする。

### tools/unittest/ → tools/unittest/ への統合

tools/unittest/ のテストファイルを tools/unittest/ に移動する。テストもツールも「開発時に実行するもの」であり、tools/ 一箇所で管理する。

### 管理台帳

`tools/README.md` を管理台帳とし、全サブディレクトリ・全ファイルの用途を記載する。台帳にないファイルは削除対象とする。CI で台帳との突合チェックを行い、差分があれば fail にする。

## サブタスク

1. [ID: P10-REORG-S1] tools/ 全スクリプトの棚卸し（不要なもの削除、用途不明なもの調査）
2. [ID: P10-REORG-S2] tools/check/, tools/gen/, tools/run/ にフォルダ分けし、既存スクリプトを移動
3. [ID: P10-REORG-S3] tools/unittest/ 全サブフォルダ・全テストファイルの棚卸し（不要なもの削除、toolchain1 残骸の特定）
4. [ID: P10-REORG-S4] tools/unittest/ を tools/unittest/ に移動し、サブフォルダを toolchain2 パイプラインに合わせて再編
5. [ID: P10-REORG-S5] 全ソース・ドキュメントの tools/ および tools/unittest/ パス参照を更新
6. [ID: P10-REORG-S6] tools/README.md を管理台帳として作成。全サブディレクトリ・全ファイルの用途を記載
7. [ID: P10-REORG-S7] CI で台帳との突合チェックを追加（台帳にないファイルがあれば fail）
8. [ID: P10-REORG-S8] AGENTS.md に「tools/ 直下への新規ファイル追加禁止」「台帳を同時更新せずにファイル追加禁止」ルールを追加

## 受け入れ基準

1. tools/ 直下にスクリプトファイルが存在しないこと
2. tools/unittest/ が tools/unittest/ に統合されていること
3. tools/README.md に全ファイルが記載されていること
4. CI で台帳突合チェックが動作すること
5. 全ソース・ドキュメントのパス参照が更新済みであること

## 決定ログ

- 2026-03-28: tools/ と tools/unittest/ の管理問題を議論。管理台帳 + CI 突合チェック + tools/ 一箇所統合の方針を決定。P10（最後の最後）として積む。
