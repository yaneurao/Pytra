<a href="../../ja/plans/p2-emit-module-root-relative-path.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/p2-emit-module-root-relative-path.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/p2-emit-module-root-relative-path.md`

# P2: emit_all_modules がモジュールにルート相対パス情報を渡す

最終更新: 2026-03-22

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P2-EMIT-ROOT-REL-PATH`

## 背景

`emit_all_modules` が `module_id.replace(".", "/")` でファイルを配置するが、サブモジュール間の相対 import パスが正しく解決されない。

例: `os/east.ps1` が `os_path/east.ps1` を参照するとき、`$PSScriptRoot`（= `out/os/`）基準だと `out/os/os_path/east.ps1` を探すが、実際は `out/os_path/east.ps1`。正しくは `../os_path/east.ps1`。

この問題は PowerShell だけでなく、Julia（`include()`）、Dart（`import`）、Zig（`@import`）等でも発生しうる。

## 設計

`emit_all_modules` が `transpile_fn` に渡す情報を拡張し、各モジュールの emit 時に以下を提供する:

- `module_id`: モジュール ID（既存）
- `root_rel_prefix`: ルートディレクトリまでの相対パス（例: `"../../"` ）
- `is_entry`: エントリモジュールかどうか（既存）

`transpile_fn` のシグネチャを `Callable[[dict, EmitContext], str]` に変更。既存の `Callable[[dict], str]` との後方互換のため、`emit_context` を EAST3 doc の `meta` に埋め込む方式も可。

## 対象

| ファイル | 変更内容 |
|---|---|
| `src/toolchain/emit/loader.py` | `emit_all_modules` で `root_rel_prefix` を計算し EAST3 doc の meta に設定 |

## 受け入れ基準

- [ ] `emit_all_modules` が各モジュールの `meta.emit_context.root_rel_prefix` を設定する
- [ ] サブモジュール（`os/east.ps1`）からの import パスが `../os_path/east.ps1` になる
- [ ] 既存 emitter がリグレッションしない

## 子タスク

- [ ] [ID: P2-EMIT-ROOT-REL-PATH-01] `emit_all_modules` で `root_rel_prefix` を計算し EAST3 doc の meta に設定する
- [ ] [ID: P2-EMIT-ROOT-REL-PATH-02] 既存テストのリグレッションがないことを検証する

## 決定ログ

- 2026-03-22: PowerShell 担当が os/east.ps1 → os_path/east.ps1 の相対パス解決失敗を報告。emitter 個別に `../` を計算するのではなく、`emit_all_modules` がルート相対パスを提供すべきと判断。
