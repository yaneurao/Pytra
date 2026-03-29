<a href="../../../en/plans/archive/20260312-p0-backends-common-foundation.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: `backends/common` 基盤導入（`CodeEmitter` + profiles 集約）

最終更新: 2026-03-03

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-BACKENDS-COMMON-FOUNDATION-01`

背景:
- 現在、共通基底の `CodeEmitter` / `EmitterHooks` は `src/pytra/compiler/east_parts/code_emitter.py` にあり、backend 実装の責務境界をまたいでいる。
- profile JSON は `src/profiles/*` に集約されている一方、backend 実装は `src/backends/<lang>/*` にあるため、配置規約が二重化している。
- backend 側を `lower / optimizer / emitter` で整理する流れに対し、共通基盤の置き場が明示されていないため、import 経路と保守導線が分散している。

目的:
- `src/backends/common/` を共通 backend 基盤の正規配置として導入する。
- `CodeEmitter` / `EmitterHooks` と共通 profile 資産を `backends/common` へ集約し、責務境界を明確化する。
- 言語別 profile は `src/backends/<lang>/profiles/` へ移し、backend ごとの自己完結性を上げる。

対象:
- 追加: `src/backends/common/`（`emitter`, `profiles`, 必要な補助モジュール）
- 移動: `CodeEmitter` / `EmitterHooks` / profile JSON（共通 + 言語別）
- 更新: import 経路（`src/backends/**`, `src/py2*.py`, `tools/**`, `test/**`）
- 更新: 仕様文書（フォルダ責務・profile 配置規約）

非対象:
- backend の機能追加・最適化ロジック変更
- EAST 仕様変更
- runtime API 仕様変更

受け入れ基準:
- `CodeEmitter` / `EmitterHooks` の正規 import が `src/backends/common/**` に統一される。
- `src/profiles/` 直参照が廃止され、profile は `src/backends/common/profiles` と `src/backends/<lang>/profiles` に整理される。
- 主要 `py2*` transpile チェックが非退行で通る。
- `docs/ja/spec`（必要に応じて `docs/en/spec`）に `backends/common` と profile 配置ルールが反映される。

確認コマンド（予定）:
- `python3 tools/check/check_todo_priority.py`
- `rg -n "pytra\\.compiler\\.east_parts\\.code_emitter|src/profiles/" src tools test`
- `python3 tools/check/check_py2cpp_transpile.py`
- `python3 tools/check/check_py2rs_transpile.py`
- `python3 tools/check/check_py2cs_transpile.py`
- `python3 tools/check/check_py2go_transpile.py`
- `python3 tools/check/check_py2java_transpile.py`
- `python3 tools/check/check_py2swift_transpile.py`
- `python3 tools/check/check_py2kotlin_transpile.py`
- `python3 tools/check/check_py2rb_transpile.py`
- `python3 tools/check/check_py2lua_transpile.py`
- `python3 tools/check/check_py2scala_transpile.py`
- `python3 tools/check/check_py2nim_transpile.py`

## 分解

- [x] [ID: P0-BACKENDS-COMMON-FOUNDATION-01-S1-01] 共通資産（`CodeEmitter` / hooks / profile loader / profile JSON）の現行配置と参照点を棚卸しする。
- [x] [ID: P0-BACKENDS-COMMON-FOUNDATION-01-S1-02] `backends/common` と `backends/<lang>/profiles` の配置規約・依存方向を定義する。
- [x] [ID: P0-BACKENDS-COMMON-FOUNDATION-01-S2-01] `src/backends/common` を新設し、`CodeEmitter` / `EmitterHooks` を移設する。
- [x] [ID: P0-BACKENDS-COMMON-FOUNDATION-01-S2-02] `src/profiles/common/*` を `src/backends/common/profiles/*` へ移設する。
- [x] [ID: P0-BACKENDS-COMMON-FOUNDATION-01-S2-03] `src/profiles/<lang>/*` を `src/backends/<lang>/profiles/*` へ移設し、参照更新する。
- [x] [ID: P0-BACKENDS-COMMON-FOUNDATION-01-S2-04] 旧 import 経路に対する互換 shim（必要最小限）を導入し、段階移行の破断を防ぐ。
- [x] [ID: P0-BACKENDS-COMMON-FOUNDATION-01-S3-01] `rg` 監査で `src/profiles/` 直参照と旧 `code_emitter` 参照の残存を解消する。
- [x] [ID: P0-BACKENDS-COMMON-FOUNDATION-01-S3-02] 主要 transpile チェックを通し、改修起因の非退行を確認する。
- [x] [ID: P0-BACKENDS-COMMON-FOUNDATION-01-S3-03] `docs/ja/spec`（必要なら `docs/en/spec`）へ責務境界とフォルダ規約を反映する。

決定ログ:
- 2026-03-03: ユーザー指示により、`src/profiles` と `CodeEmitter` の分散配置を見直し、`backends/common` を最優先（P0）で導入する方針を確定。
- 2026-03-03: `CodeEmitter` / `EmitterHooks` の正規実装を `src/backends/common/emitter/code_emitter.py` へ移し、旧 `src/pytra/compiler/east_parts/code_emitter.py` は互換 shim 化した。
- 2026-03-03: profile JSON を `src/backends/common/profiles` と `src/backends/{cpp,rs,cs,js}/profiles` へ移設し、各 emitter・テスト・version gate の参照を新パスへ更新した。
- 2026-03-03: `rg` 監査で `src/profiles` と旧 `code_emitter` 直参照（import）の残存がないことを確認し、`check_py2{cpp,rs,cs,js,go,java,swift,kotlin,rb,lua,scala,ts,nim}_transpile.py` と `check_transpiler_version_gate.py` の通過を確認した。
- 2026-03-03: `docs/ja/spec` / `docs/en/spec` の `src/profiles`・`src/common`・旧 `code_emitter` 記述を `src/backends/**/profiles`・`src/backends/common`・新 `code_emitter` パスへ更新し、責務境界記述を現状実装へ同期した。
