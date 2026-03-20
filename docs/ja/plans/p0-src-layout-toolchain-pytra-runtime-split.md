# P0: `src` レイアウト再編（`toolchain` / `pytra` / `runtime`）

最終更新: 2026-03-03

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-SRC-LAYOUT-SPLIT-01`

背景:
- 現在 `src/pytra` には、変換プログラム本体（`frontends` / `ir` / `compiler`）と、変換時に参照するライブラリ定義（`std` / `utils` / `built_in`）が同居している。
- 一方 `src/runtime` は変換後コードの実行時に使われる成果物であり、責務が明確に異なる。
- フォルダ責務が混在しているため、開発時に「どこを編集すべきか」の判断コストが高い。

目的:
- `src` を責務別に 3 系統へ再編し、境界を明確化する。
  - `src/toolchain`: 変換プログラム本体
  - `src/pytra`: 変換時参照ライブラリ（Python名前空間）
  - `src/runtime`: 変換後実行ランタイム
- `src/pytra` から `frontends` / `ir` / `compiler` を外し、`pytra` 配下は `std` / `utils` / `built_in` を中心に維持する。
- 後方互換レイヤは作らず、正規パスへ一括切替する。

対象:
- ディレクトリ移動:
  - `src/pytra/frontends/** -> src/toolchain/frontends/**`
  - `src/pytra/ir/** -> src/toolchain/ir/**`
  - `src/pytra/compiler/** -> src/toolchain/compiler/**`
- import 更新:
  - `src/`, `tools/`, `test/` の旧 `pytra.frontends` / `pytra.ir` / `pytra.compiler` 参照を新経路へ更新
- ドキュメント更新:
  - `docs/ja/spec/*`（必要に応じて `docs/en/spec/*`）

非対象:
- backend 機能追加・最適化ロジック変更
- runtime API 仕様変更
- sample ベンチマーク値更新

後方互換方針:
- 旧 import 経路の re-export shim は作らない。
- 旧パス参照は一括で削除・置換し、残存は失敗として扱う。

受け入れ基準:
- `src/toolchain/{frontends,ir,compiler}` が存在し、旧 `src/pytra/{frontends,ir,compiler}` は存在しない。
- `src/pytra` は `std` / `utils` / `built_in` 中心の構成へ収束している。
- リポジトリ内に `from pytra.frontends` / `from pytra.ir` / `from pytra.compiler` の旧参照が残らない（意図的例外なし）。
- 主要 transpile / unit 回帰が通る。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `rg -n "pytra\\.(frontends|ir|compiler)" src tools test`
- `python3 tools/check_pytra_layer_boundaries.py`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/check_py2rs_transpile.py`
- `python3 tools/check_py2js_transpile.py`
- `python3 tools/check_py2ts_transpile.py`
- `python3 tools/check_py2go_transpile.py`
- `python3 tools/check_py2java_transpile.py`
- `python3 tools/check_py2kotlin_transpile.py`
- `python3 tools/check_py2swift_transpile.py`
- `python3 tools/check_py2rb_transpile.py`
- `python3 tools/check_py2lua_transpile.py`
- `python3 tools/check_py2scala_transpile.py`
- `python3 tools/check_py2php_transpile.py`
- `python3 tools/check_py2nim_transpile.py`

## 分解

- [x] [ID: P0-SRC-LAYOUT-SPLIT-01-S1-01] 現行 `src/pytra/{frontends,ir,compiler,std,utils,built_in}` の責務と参照点を棚卸しする。
- [x] [ID: P0-SRC-LAYOUT-SPLIT-01-S1-02] 新レイアウト規約（`toolchain` / `pytra` / `runtime`）と依存方向を `docs/ja/spec/spec-folder.md` に確定する。
- [x] [ID: P0-SRC-LAYOUT-SPLIT-01-S1-03] 旧 import 経路を禁止する移行ルール（後方互換なし）を明文化する。
- [x] [ID: P0-SRC-LAYOUT-SPLIT-01-S2-01] `src/toolchain/frontends` を作成し、`src/pytra/frontends` を一括移動する。
- [x] [ID: P0-SRC-LAYOUT-SPLIT-01-S2-02] `src/toolchain/ir` を作成し、`src/pytra/ir` を一括移動する。
- [x] [ID: P0-SRC-LAYOUT-SPLIT-01-S2-03] `src/toolchain/compiler` を作成し、`src/pytra/compiler` を一括移動する。
- [x] [ID: P0-SRC-LAYOUT-SPLIT-01-S2-04] `src/pytra` 配下の空ディレクトリ・不要残骸を除去し、`std/utils/built_in` 中心構成へ整理する。
- [x] [ID: P0-SRC-LAYOUT-SPLIT-01-S3-01] `src/`, `tools/`, `test/` の import を新経路へ一括更新する（shim 追加禁止）。
- [x] [ID: P0-SRC-LAYOUT-SPLIT-01-S3-02] CLI エントリ（`py2x.py`, `py2x-selfhost.py`, `py2*.py`）の import 経路を新構成に合わせる。
- [x] [ID: P0-SRC-LAYOUT-SPLIT-01-S3-03] 検査スクリプトを追加し、旧 `pytra.frontends|ir|compiler` 参照を fail-fast で検出する。
- [x] [ID: P0-SRC-LAYOUT-SPLIT-01-S4-01] 主要 unit/transpile 回帰を実行し、非退行を確認する。
- [x] [ID: P0-SRC-LAYOUT-SPLIT-01-S4-02] `docs/ja/spec`（必要なら `docs/en/spec`）へ新ディレクトリ責務と導線を反映する。

## S1-01 棚卸し結果

### `src/pytra` 配下の責務（現状）

| 領域 | `.py` ファイル数 | 主責務 | 主な外部参照点 |
|---|---:|---|---|
| `frontends` | 7 | Python入力の解析・import graph 構築・シグネチャ/semantic 判定 | `src/py2cpp.py`, `pytra.compiler.transpile_cli`, `pytra.ir.core` |
| `ir` | 30 | EAST1/2/3 定義・lower・optimizer・pipeline | `pytra.frontends.transpile_cli`, `pytra.compiler.east_parts.*` |
| `compiler` | 44 | 互換 shim・backend registry・CLI 補助・`east_parts` 互換レイヤ | `src/py2*.py`, `src/ir2lang.py`, `tools/*`, `test/unit/*` |
| `std` | 19 | 変換時に解決する std 互換層（`typing/pathlib/json/...`） | `src/py2*.py`, `src/toolchain/emit/*`, `test/fixtures/stdlib/*` |
| `utils` | 4 | 変換対象コード側で使う helper（`assertions/png/gif`） | `sample/py/*`, `test/fixtures/*`, `tools/verify_image_runtime_parity.py` |
| `built_in` | 2 | built-in 互換補助（`type_id` など） | `test/unit/test_pytra_built_in_type_id.py` |

### 参照点の実測（`src/tools/test`）

- `frontends`: 105 参照（`src:104 / tools:0 / test:1`）
- `ir`: 247 参照（`src:246 / tools:0 / test:1`）
- `compiler`: 275 参照（`src:102 / tools:10 / test:163`）
- `std`: 526 参照（`src:432 / tools:2 / test:92`）
- `utils`: 211 参照（`src:0 / tools:1 / test:210`）
- `built_in`: 1 参照（`src:0 / tools:0 / test:1`）

### 依存方向の所見（S2/S3 で解消対象）

- `frontends -> ir` と `ir -> frontends` が共存しており、循環参照が存在する（`transpile_cli` と `ir.core` が相互依存）。
- `compiler` は既に互換 shim 層として機能しており、`src/py2*.py` / `tools` / `test` からの集中依存点になっている。
- `std/utils/built_in` は変換実行時の参照ライブラリとして広く使われているため、`toolchain` 側へ移す対象ではない。

決定ログ:
- 2026-03-03: ユーザー指示により、`src` の責務境界を `toolchain` / `pytra` / `runtime` の3系統へ再編する計画を P0 として起票。
- 2026-03-03: 後方互換レイヤ（旧 import re-export）は不要と判断し、移行時に旧経路を一括撤去する方針を採用。
- 2026-03-03: [ID: P0-SRC-LAYOUT-SPLIT-01-S1-01] `src/pytra` 6領域の責務と参照点を棚卸しし、`compiler` への依存集中と `frontends`/`ir` の循環参照を確認した。
- 2026-03-03: [ID: P0-SRC-LAYOUT-SPLIT-01-S1-02] `docs/ja/spec/spec-folder.md` を更新し、`src/toolchain/{frontends,ir,compiler}` を正規配置、`src/pytra` を参照ライブラリ専用とする依存方向を確定した。
- 2026-03-03: [ID: P0-SRC-LAYOUT-SPLIT-01-S1-03] `spec-folder` に旧 import 経路禁止規約（`pytra.frontends|ir|compiler` 新規追加禁止、shim 追加禁止、`rg` 検査手順）を追記した。
- 2026-03-03: [ID: P0-SRC-LAYOUT-SPLIT-01-S2-01] `src/toolchain/frontends` を新設し、`src/pytra/frontends/*.py` を移動。参照先 import を `toolchain.frontends.*` へ更新し、`tools/check_pytra_layer_boundaries.py` と `test_pytra_layer_bootstrap` の通過を確認した。
- 2026-03-03: [ID: P0-SRC-LAYOUT-SPLIT-01-S2-02] `src/toolchain/ir` を新設し、`src/pytra/ir/*.py` を移動。`frontends`/`compiler.east_parts`/`test`/`tools` の参照先を `toolchain.ir.*` に更新し、`check_pytra_layer_boundaries`・`test_pytra_layer_bootstrap`・`py2cpp/py2x` 変換スモークの通過を確認した。
- 2026-03-03: [ID: P0-SRC-LAYOUT-SPLIT-01-S2-03] `src/toolchain/compiler` を新設し、`src/pytra/compiler` を移動。`py2x/py2*.py`・`toolchain/emit/cpp`・`tools`・`test`・`selfhost` の import を `toolchain.compiler.*` へ切替え、`prepare_selfhost_source`/`signature_registry`/`east_stage_boundary` など固定パス依存も新配置へ更新した。
- 2026-03-03: [ID: P0-SRC-LAYOUT-SPLIT-01-S2-04] `src/pytra` 配下から `frontends`/`ir`/`compiler` ディレクトリが消えていることを確認し、`pytra` は `std`/`utils`/`built_in` と最小エントリ（`__init__.py`, `cli.py`）のみへ収束した。
- 2026-03-03: [ID: P0-SRC-LAYOUT-SPLIT-01-S3-01] `src/tools/test/selfhost` の import を新経路へ一括更新し、`rg` により旧 `pytra.frontends|pytra.ir|pytra.compiler`（`src.pytra.*` 含む）import が 0 件であることを確認した。
- 2026-03-03: [ID: P0-SRC-LAYOUT-SPLIT-01-S3-02] `py2x.py` / `py2x-selfhost.py` / `py2*.py` / `ir2lang.py` の import を `toolchain.compiler.*` へ統一し、CLI エントリから旧 `pytra.compiler` 依存を排除した。
- 2026-03-03: [ID: P0-SRC-LAYOUT-SPLIT-01-S3-03] `tools/check_pytra_layer_boundaries.py` に legacy import スキャン（`src/tools/test/selfhost` 対象）を追加し、`pytra.frontends|pytra.ir|pytra.compiler`（`src.pytra.*` 含む）を `legacy import path is forbidden` として fail-fast 検出するようにした（syntax error fixture はスキップ）。
- 2026-03-03: [ID: P0-SRC-LAYOUT-SPLIT-01-S4-01] 主要回帰を実行し、`check_east_stage_boundary`/`check_pytra_layer_boundaries` と `check_py2{cpp,rs,js,ts,go,java,kotlin,swift,rb,lua,scala,php,nim}_transpile.py` がすべて pass（fail=0）であることを確認した。
- 2026-03-03: [ID: P0-SRC-LAYOUT-SPLIT-01-S4-02] `docs/ja/spec` と `docs/en/spec`（`archive` 除く）を走査し、旧 `src/pytra/{frontends,ir,compiler}` パス参照を `src/toolchain/{frontends,ir,compiler}` へ更新して導線を現行実装へ一致させた。
