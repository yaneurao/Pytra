<a href="../../en/plans/p0-py2x-dual-entrypoints-host-selfhost.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: `py2x` エントリ分離（通常 `pytra-cli.py` / selfhost `pytra-cli.py`）

最終更新: 2026-03-03

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-PY2X-DUAL-ENTRYPOINT-01`

背景:
- 通常実行では target backend のみを lazy import したい一方、selfhost 実行では動的 import が使えず static import が必要。
- 単一エントリで両要件を同時に満たそうとすると、`if` 分岐 import など selfhost 非互換実装が混入しやすい。
- 役割分離として、通常実行用と selfhost 用のエントリを分ける構成が必要。

目的:
- `pytra-cli.py` を「通常実行専用（host, lazy import）」へ明確化する。
- `pytra-cli.py` を「selfhost専用（static eager import）」として分離し、selfhost互換を固定する。
- 既存 `py2*.py` ラッパは通常系 (`pytra-cli.py`) を継続利用し、挙動差分を最小化する。

対象:
- `src/pytra-cli.py`（通常系）
- `src/pytra-cli.py`（新規）
- backend registry の lazy/eager 構成
- selfhost 関連の実行導線（必要最小限）
- docs（使い分け規約）

非対象:
- backend 生成品質改善
- runtime API 仕様変更
- selfhost 失敗ケースの全面改修

受け入れ基準:
- 通常利用は `pytra-cli.py` で target 単位 lazy import が有効。
- selfhost 利用は `pytra-cli.py` で static import のみで動作し、動的 import を含まない。
- 既存 `py2*.py` ラッパの通常利用導線は非退行。
- docs に「通常/ selfhost のエントリ使い分け」が明記されている。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 -m unittest discover -s test/unit -p test_py2x_cli.py`
- `python3 tools/check_py2rs_transpile.py`
- `python3 tools/check_py2js_transpile.py`
- `python3 tools/check_py2php_transpile.py`
- `python3 tools/check_py2scala_transpile.py`
- `python3 tools/check_py2nim_transpile.py`

## 分解

- [x] [ID: P0-PY2X-DUAL-ENTRYPOINT-01-S1-01] 現行 `py2x` 導線（通常実行/selfhost実行）の import 制約と責務境界を棚卸しする。
- [x] [ID: P0-PY2X-DUAL-ENTRYPOINT-01-S1-02] `pytra-cli.py`（host）と `pytra-cli.py`（selfhost）の契約（許可/禁止事項）を定義する。
- [x] [ID: P0-PY2X-DUAL-ENTRYPOINT-01-S2-01] `pytra-cli.py` を host-lazy 専用実装へ整理する（selfhost 条件分岐を排除）。
- [x] [ID: P0-PY2X-DUAL-ENTRYPOINT-01-S2-02] `pytra-cli.py` を新設し、static eager import のみで同等CLIを提供する。
- [x] [ID: P0-PY2X-DUAL-ENTRYPOINT-01-S2-03] backend registry 依存を host/selfhost で分離し、境界違反を検知できる形にする。
- [x] [ID: P0-PY2X-DUAL-ENTRYPOINT-01-S3-01] unit/transpile 回帰を実行し、通常導線の非退行を確認する。
- [x] [ID: P0-PY2X-DUAL-ENTRYPOINT-01-S3-02] selfhost 用導線の smoke/最小回帰を実行し、動的 import 非依存を確認する。
- [x] [ID: P0-PY2X-DUAL-ENTRYPOINT-01-S3-03] docs に使い分けと移行手順を追記する。

決定ログ:
- 2026-03-03: 「通常は `pytra-cli.py`（lazy）、selfhost は `pytra-cli.py`（static）」の二系統分離方針を採用。
- 2026-03-03: 現行棚卸しとして、`src/pytra-cli.py` が `pytra.compiler.backend_registry`（全backend eager import）へ依存し、`py2*.py` ラッパが `pytra.compiler.py2x_wrapper.run_py2x_for_target` 経由で通常導線を共有していることを確認した。
- 2026-03-03: 契約を次で固定した。host (`pytra-cli.py`) は dynamic import 許可・target限定 lazy import 必須。selfhost (`pytra-cli.py`) は dynamic import 禁止・static eager import のみ許可。両者とも CLI 契約（`--target`, layer options, EAST3固定）は同一に保つ。
- 2026-03-03: `src/pytra/compiler/backend_registry.py` を host-lazy registry に差し替え、`importlib.import_module` + target別 loader + `_SPEC_CACHE` で必要 backend のみ遅延ロードする構成へ変更した。従来の eager registry は `src/pytra/compiler/backend_registry_static.py` として分離した。
- 2026-03-03: `src/pytra-cli.py` を追加し、`backend_registry_static` を参照する selfhost 専用エントリを新設した。`src/pytra-cli.py` は `backend_registry`（host-lazy）固定の通常導線とした。
- 2026-03-03: import cycle 回避のため、`src/pytra/compiler/east_parts/__init__.py` から `east1_build` の package-level re-export を外し、明示 import のみを許可する形へ変更した。
- 2026-03-03: 境界違反検知として `test/unit/test_py2x_entrypoints_contract.py` を追加し、`py2x`/`py2x-selfhost` の registry バインディング、host registry の lazy import 方式、target限定 import、spec cache 利用を unit 固定した。
- 2026-03-03: 回帰確認として次を実行し、すべて通過した。`test_py2x_cli.py`, `test_py2x_entrypoints_contract.py`, `check_py2{rs,js,php,scala,nim}_transpile.py`, `check_noncpp_east3_contract.py --skip-transpile`, `check_transpiler_version_gate.py --base-ref HEAD`。
- 2026-03-03: `docs/ja/how-to-use.md` と `docs/en/how-to-use.md` に `pytra-cli.py` / `pytra-cli.py` の使い分け（通常=host-lazy, selfhost=static eager）を追記した。
