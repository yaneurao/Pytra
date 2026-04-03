# P10-LEGACY-TOOLCHAIN-REMOVAL: 旧 toolchain + pytra-cli.py を削除する

最終更新: 2026-04-03

## 背景

Pytra のトランスパイルパイプラインは旧 toolchain（`src/toolchain/`）から新 toolchain2（`src/toolchain2/`）に移行中。CLI も旧 `src/pytra-cli.py` から `src/pytra-cli2.py` に移行済み。

全18言語の emitter が toolchain2 に実装（P1-*-EMITTER-S1 完了）された時点で、旧パイプラインへの依存がゼロになるため、削除できる。

## 前提条件（ゲート）

全言語の toolchain2 emitter 実装が完了していること。具体的には各言語の `src/toolchain2/emit/<lang>/emitter.py` が存在し、`cli.py` 経由で parity check が動作すること。

2026-04-03 時点の状況:
- 完了: C++ / Rust / C# / TS-JS / Go / Java / Ruby / Lua / PHP / Nim / Dart / Scala / Kotlin / Swift
- 進行中: Julia（fixture 85/145）
- 未完了: Zig（fixture 進行中）
- 着手済み: PowerShell（S1-S3 完了、S4 以降未着手）

## 削除対象

### `src/toolchain/`（旧 emitter + compile + frontends）

| ディレクトリ | 内容 |
|---|---|
| `src/toolchain/emit/<lang>/` | 各言語の旧 emitter（全18言語分） |
| `src/toolchain/compile/` | 旧 compile パス |
| `src/toolchain/frontends/` | 旧 CLI フロントエンド（`transpile_cli.py` 等） |
| `src/toolchain/misc/` | 旧 EAST 生成（`east.py` 等） |
| `src/toolchain/link/` | 旧 linker（存在する場合） |

### `src/pytra-cli.py`（旧 CLI）

削除後、`src/pytra-cli2.py` を `src/pytra-cli.py` にリネーム。

### 参照箇所の更新

- `docs/ja/spec/` — emitter guide は更新済み（旧 toolchain 参照は 2026-04-03 に削除済み）
- `docs/ja/tutorial/` — `pytra-cli.py` → `pytra-cli2.py` の参照（リネーム後に戻す）
- `tools/run/run_local_ci.py` — 旧パイプライン参照があれば削除
- `tools/README.md` — ツール台帳の旧パイプライン参照
- `test/` — 旧パイプラインを使うテスト（移行 or 削除）
- `README.md` / `docs/ja/README.md` — CLI 名の更新

## 注意事項

- **削除は一括で行う。** 段階的に「一部の旧 emitter だけ消す」はやらない。参照が残って壊れるリスクが高い
- **削除前に `git tag v0.x-pre-toolchain-removal` を打つ。** 万一戻す必要がある場合に備える
- **旧 toolchain に依存する test がないことを確認してから削除。** `grep -r "from toolchain\." tools/ test/` で依存を洗い出す
- **selfhost golden は toolchain2 で再生成。** 旧 toolchain で生成された golden が残っていないことを確認
- **`pytra-cli2.py` → `pytra-cli.py` リネーム後、全ドキュメントの CLI 名を更新。** `pytra-cli2` への参照を全て `pytra-cli` に置換

## サブタスク

1. [ ] [ID: P10-LEGACY-RM-S1] 全言語の P1-*-EMITTER-S1 完了を確認する（ゲート）
2. [ ] [ID: P10-LEGACY-RM-S2] `src/toolchain/` を削除する
3. [ ] [ID: P10-LEGACY-RM-S3] `src/pytra-cli.py` を削除し、`src/pytra-cli2.py` を `src/pytra-cli.py` にリネームする
4. [ ] [ID: P10-LEGACY-RM-S4] spec / tutorial / README の旧パイプライン参照を更新する
5. [ ] [ID: P10-LEGACY-RM-S5] `run_local_ci.py` 等のツールから旧パイプライン参照を削除する

## 決定ログ

- 2026-04-03: 全言語の cli.py を共通ランナーに移行完了。旧 toolchain への依存は parity check（tools/、動的 import で解決済み）と一部の test のみ。ゲート条件（Julia / Zig / PowerShell の S1 完了）が揃い次第、削除に着手。
