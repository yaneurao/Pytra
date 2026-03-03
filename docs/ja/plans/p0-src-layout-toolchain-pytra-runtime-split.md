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

- [ ] [ID: P0-SRC-LAYOUT-SPLIT-01-S1-01] 現行 `src/pytra/{frontends,ir,compiler,std,utils,built_in}` の責務と参照点を棚卸しする。
- [ ] [ID: P0-SRC-LAYOUT-SPLIT-01-S1-02] 新レイアウト規約（`toolchain` / `pytra` / `runtime`）と依存方向を `docs/ja/spec-folder.md` に確定する。
- [ ] [ID: P0-SRC-LAYOUT-SPLIT-01-S1-03] 旧 import 経路を禁止する移行ルール（後方互換なし）を明文化する。
- [ ] [ID: P0-SRC-LAYOUT-SPLIT-01-S2-01] `src/toolchain/frontends` を作成し、`src/pytra/frontends` を一括移動する。
- [ ] [ID: P0-SRC-LAYOUT-SPLIT-01-S2-02] `src/toolchain/ir` を作成し、`src/pytra/ir` を一括移動する。
- [ ] [ID: P0-SRC-LAYOUT-SPLIT-01-S2-03] `src/toolchain/compiler` を作成し、`src/pytra/compiler` を一括移動する。
- [ ] [ID: P0-SRC-LAYOUT-SPLIT-01-S2-04] `src/pytra` 配下の空ディレクトリ・不要残骸を除去し、`std/utils/built_in` 中心構成へ整理する。
- [ ] [ID: P0-SRC-LAYOUT-SPLIT-01-S3-01] `src/`, `tools/`, `test/` の import を新経路へ一括更新する（shim 追加禁止）。
- [ ] [ID: P0-SRC-LAYOUT-SPLIT-01-S3-02] CLI エントリ（`py2x.py`, `py2x-selfhost.py`, `py2*.py`）の import 経路を新構成に合わせる。
- [ ] [ID: P0-SRC-LAYOUT-SPLIT-01-S3-03] 検査スクリプトを追加し、旧 `pytra.frontends|ir|compiler` 参照を fail-fast で検出する。
- [ ] [ID: P0-SRC-LAYOUT-SPLIT-01-S4-01] 主要 unit/transpile 回帰を実行し、非退行を確認する。
- [ ] [ID: P0-SRC-LAYOUT-SPLIT-01-S4-02] `docs/ja/spec`（必要なら `docs/en/spec`）へ新ディレクトリ責務と導線を反映する。

決定ログ:
- 2026-03-03: ユーザー指示により、`src` の責務境界を `toolchain` / `pytra` / `runtime` の3系統へ再編する計画を P0 として起票。
- 2026-03-03: 後方互換レイヤ（旧 import re-export）は不要と判断し、移行時に旧経路を一括撤去する方針を採用。
