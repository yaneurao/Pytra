# P1-PARITY-CONSOLIDATION: runtime_parity_check.py を fast 版に統合する

最終更新: 2026-04-14

## 背景

parity check ツールが 2 本並存している。

| ファイル | 方式 | 行数 |
|---|---|---|
| `tools/check/runtime_parity_check.py` | `pytra-cli.py` を subprocess で呼ぶ | ~1040 |
| `tools/check/runtime_parity_check_fast.py` | toolchain2 in-memory API で直接実行 | ~1500 |

fast 版が全言語の日常検証で使われており、旧版は実質メンテナンスされていない。
旧版には `target="js"` を lowering に渡す際の `"js"` → `"ts"` マッピング漏れがあり、JS parity が常に失敗する（`profiles/js.json` 欠落）。
Go/Rust 等は旧版でも動くが、fast 版と旧版の挙動差が拡大しつつあり、二重メンテのコストが正当化できなくなっている。

## 目的

- `runtime_parity_check_fast.py` を正本に一本化する
- 旧版に依存するスクリプトとドキュメントを全て切り替える
- 旧版を削除する

## 影響範囲

### コード参照（旧版を直接呼んでいる箇所）

1. `tools/check/check_noncpp_backend_health.py` — subprocess で旧版を呼んでいる
2. `tools/gen/regenerate_samples.py` — 旧版パスを参照
3. `tools/unittest/tooling/test_runtime_parity_check_cli.py` — 旧版のテスト

### ドキュメント参照（20箇所以上）

- `docs/ja/tutorial/transpiler-cli.md`
- `docs/ja/tutorial/dev-operations.md`
- `docs/en/tutorial/transpiler-cli.md`
- `docs/en/tutorial/dev-operations.md`
- `sample/README.md` / `sample/README-ja.md`
- `tools/README.md`
- `docs/ja/spec/spec-tools.md`（tools 一覧）
- その他 progress/archive 内の歴史的参照

## サブタスク

### S1: check_noncpp_backend_health.py の切り替え

`check_noncpp_backend_health.py` が旧版を subprocess 呼びしている箇所を fast 版に切り替える。
fast 版の CLI インターフェースが旧版と互換であることを確認し、必要ならオプションを調整する。

### S2: regenerate_samples.py の切り替え

`regenerate_samples.py` 内の旧版参照を fast 版に変更する。

### S3: ドキュメント一括更新

`docs/ja/` と `docs/en/` のチュートリアル・README・spec-tools.md 内のコマンド例を fast 版に書き換える。
歴史的記述（archive 内の完了ログ等）はそのまま残す。

### S4: fast 版のリネーム検討

統合後に `_fast` サフィックスが不要になるため、`runtime_parity_check.py` にリネームするか検討する。
リネームする場合は S1〜S3 の参照を新名に合わせる。

### S5: 旧版削除とテスト整理

旧版 `runtime_parity_check.py` を削除する。
`test_runtime_parity_check_cli.py` の旧版テストを削除または fast 版テストに統合する。

### S6: pytra-cli.py の js→ts マッピング修正

旧版削除とは別に、`pytra-cli.py` の `_build_pipeline` で `target="js"` を `target_language="ts"` に変換する修正を入れる。
これは旧版削除前でも独立して実施可能。

## 決定ログ

- 2026-04-14: 旧版の JS parity 失敗を契機に調査。fast 版への統合方針を決定。
- 2026-04-14: `check_noncpp_backend_health.py` と `regenerate_samples.py` の parity 呼び出しは fast 版へ切替。`pytra-cli.py` の `_build_pipeline()` に `js -> ts` lowering マッピングを追加した。
- 2026-04-14: 利用者向けの正規コマンド名は `runtime_parity_check.py` に維持する。物理リネームは行わず、`runtime_parity_check.py` を fast 実装へ委譲する互換エントリ、`runtime_parity_check_fast.py` を互換エイリアスとして残す。
