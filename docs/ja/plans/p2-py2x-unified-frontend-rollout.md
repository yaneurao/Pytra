# P2: `py2x.py` 一本化 frontend 導入（層別 option pass-through）

最終更新: 2026-03-02

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P2-PY2X-UNIFIED-FRONTEND-01`

背景:
- 現状は `py2cpp.py`, `py2cs.py`, `py2rs.py` など言語別 frontend が個別に存在し、入力処理/EAST3 変換/CLI 解析/出力配置の重複が多い。
- 一方で「入力 Python -> EAST3」までは共通責務であり、backend 差分は本来 `lower/optimizer/emitter/extensions` 側へ寄せるべきである。
- ユーザー要件として、層ごとに frontend から option を渡せる共通インタフェース（`--lower-option`, `--optimizer-option`, `--emitter-option`）を採用する。

目的:
- `py2x.py` を共通 frontend として導入し、言語差分を backend registry と層別 option schema に集約する。
- 既存 `py2*.py` は互換ラッパへ段階縮退し、重複した CLI/EAST3 前処理実装を削減する。

対象:
- 新規: `src/py2x.py`
- 新規: backend registry（例: `src/pytra/compiler/backend_registry.py`）
- 更新: 既存 `py2*.py`（thin wrapper 化）
- 更新: docs（`how-to-use`, `spec-dev`, `spec-folder`, CLI 使用例）
- 更新: transpile check ツール群（`py2x` 導線検証）

非対象:
- backend の生成品質改善そのもの（emit 内容変更）
- EAST1/EAST2/EAST3 仕様変更
- 既存 `py2*.py` の即時削除（互換期間は維持）

受け入れ基準:
- `py2x.py --target <lang>` で既存対応言語（少なくとも `cpp/rs/cs/js/ts/go/java/swift/kotlin/ruby/lua/scala/php`）を呼び分けできる。
- `--lower-option`, `--optimizer-option`, `--emitter-option` で `key=value` を backend 層へ透過伝達できる。
- 層別 option は backend 側 schema で検証され、未知キー/型不正は fail-fast する。
- 既存 `py2*.py` は同等挙動を維持しつつ `py2x` 呼び出しへ縮退する。
- 主要 transpile check と unit が非退行で通る。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 src/py2x.py --help`
- `python3 src/py2x.py sample/py/01_mandelbrot.py --target cpp -o out/tmp_01.cpp`
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

## 分解

- [ ] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S1-01] 現行 `py2*.py` の CLI 差分と runtime 配置差分を棚卸しし、共通 frontend 化で残す差分を確定する。
- [ ] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S1-02] `py2x` 共通 CLI 仕様を策定する（`--target`, 層別 option, 互換オプション, fail-fast 規約）。
- [ ] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S1-03] backend registry 契約（entrypoint, default options, option schema, runtime packaging hook）を定義する。
- [ ] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S2-01] `py2x.py` を実装し、共通入力処理（`.py/.json -> EAST3`）と target dispatch を導入する。
- [ ] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S2-02] 層別 option parser（`--lower-option`, `--optimizer-option`, `--emitter-option`）と schema 検証を実装する。
- [ ] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S2-03] 既存 `py2*.py` を thin wrapper 化し、互換 CLI を `py2x` 呼び出しへ委譲する。
- [ ] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S2-04] runtime/packaging 差分を backend extensions hook へ移し、frontend 側分岐を削減する。
- [ ] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S3-01] CLI 単体テストを追加し、target dispatch と層別 option 伝搬を固定する。
- [ ] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S3-02] 既存 transpile check 群を `py2x` 経由でも通し、言語横断で非退行を確認する。
- [ ] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S3-03] `docs/ja` / `docs/en` の使い方・仕様を更新し、移行手順（互換ラッパ期間を含む）を明文化する。

決定ログ:
- 2026-03-02: ユーザー指示により、言語別 frontend の重複を解消するため `py2x.py` 一本化計画を P2 として起票。
- 2026-03-02: option 指定は層別 pass-through（`--lower-option`, `--optimizer-option`, `--emitter-option`）を正とし、backend schema 検証の fail-fast を採用。
