# P0: `py2x` エントリ分離（通常 `py2x.py` / selfhost `py2x-selfhost.py`）

最終更新: 2026-03-03

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-PY2X-DUAL-ENTRYPOINT-01`

背景:
- 通常実行では target backend のみを lazy import したい一方、selfhost 実行では動的 import が使えず static import が必要。
- 単一エントリで両要件を同時に満たそうとすると、`if` 分岐 import など selfhost 非互換実装が混入しやすい。
- 役割分離として、通常実行用と selfhost 用のエントリを分ける構成が必要。

目的:
- `py2x.py` を「通常実行専用（host, lazy import）」へ明確化する。
- `py2x-selfhost.py` を「selfhost専用（static eager import）」として分離し、selfhost互換を固定する。
- 既存 `py2*.py` ラッパは通常系 (`py2x.py`) を継続利用し、挙動差分を最小化する。

対象:
- `src/py2x.py`（通常系）
- `src/py2x-selfhost.py`（新規）
- backend registry の lazy/eager 構成
- selfhost 関連の実行導線（必要最小限）
- docs（使い分け規約）

非対象:
- backend 生成品質改善
- runtime API 仕様変更
- selfhost 失敗ケースの全面改修

受け入れ基準:
- 通常利用は `py2x.py` で target 単位 lazy import が有効。
- selfhost 利用は `py2x-selfhost.py` で static import のみで動作し、動的 import を含まない。
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

- [ ] [ID: P0-PY2X-DUAL-ENTRYPOINT-01-S1-01] 現行 `py2x` 導線（通常実行/selfhost実行）の import 制約と責務境界を棚卸しする。
- [ ] [ID: P0-PY2X-DUAL-ENTRYPOINT-01-S1-02] `py2x.py`（host）と `py2x-selfhost.py`（selfhost）の契約（許可/禁止事項）を定義する。
- [ ] [ID: P0-PY2X-DUAL-ENTRYPOINT-01-S2-01] `py2x.py` を host-lazy 専用実装へ整理する（selfhost 条件分岐を排除）。
- [ ] [ID: P0-PY2X-DUAL-ENTRYPOINT-01-S2-02] `py2x-selfhost.py` を新設し、static eager import のみで同等CLIを提供する。
- [ ] [ID: P0-PY2X-DUAL-ENTRYPOINT-01-S2-03] backend registry 依存を host/selfhost で分離し、境界違反を検知できる形にする。
- [ ] [ID: P0-PY2X-DUAL-ENTRYPOINT-01-S3-01] unit/transpile 回帰を実行し、通常導線の非退行を確認する。
- [ ] [ID: P0-PY2X-DUAL-ENTRYPOINT-01-S3-02] selfhost 用導線の smoke/最小回帰を実行し、動的 import 非依存を確認する。
- [ ] [ID: P0-PY2X-DUAL-ENTRYPOINT-01-S3-03] docs に使い分けと移行手順を追記する。

決定ログ:
- 2026-03-03: 「通常は `py2x.py`（lazy）、selfhost は `py2x-selfhost.py`（static）」の二系統分離方針を採用。
