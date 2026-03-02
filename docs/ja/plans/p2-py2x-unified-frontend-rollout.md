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

- [x] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S1-01] 現行 `py2*.py` の CLI 差分と runtime 配置差分を棚卸しし、共通 frontend 化で残す差分を確定する。
- [x] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S1-02] `py2x` 共通 CLI 仕様を策定する（`--target`, 層別 option, 互換オプション, fail-fast 規約）。
- [ ] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S1-03] backend registry 契約（entrypoint, default options, option schema, runtime packaging hook）を定義する。
- [ ] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S2-01] `py2x.py` を実装し、共通入力処理（`.py/.json -> EAST3`）と target dispatch を導入する。
- [ ] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S2-02] 層別 option parser（`--lower-option`, `--optimizer-option`, `--emitter-option`）と schema 検証を実装する。
- [ ] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S2-03] 既存 `py2*.py` を thin wrapper 化し、互換 CLI を `py2x` 呼び出しへ委譲する。
- [ ] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S2-04] runtime/packaging 差分を backend extensions hook へ移し、frontend 側分岐を削減する。
- [ ] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S3-01] CLI 単体テストを追加し、target dispatch と層別 option 伝搬を固定する。
- [ ] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S3-02] 既存 transpile check 群を `py2x` 経由でも通し、言語横断で非退行を確認する。
- [ ] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S3-03] `docs/ja` / `docs/en` の使い方・仕様を更新し、移行手順（互換ラッパ期間を含む）を明文化する。

## S1-01 棚卸し結果（2026-03-03）

### CLI 差分

| 区分 | 対象 | 現状 | `py2x` での扱い |
| --- | --- | --- | --- |
| 共通 CLI | `py2cs/rs/js/ts/go/java/kotlin/swift/rb/lua/php/scala/nim` | `INPUT`, `-o/--output`, `--parser-backend`, `--east-stage`, `--object-dispatch-mode`, EAST3 optimizer 系 dump/level | `py2x` の共通引数として統合する。 |
| C# だけ独自実装 | `py2cs.py` | `argparse` 非使用の手書き parser | `py2x` 側で argparse 統一し、`py2cs.py` は互換ラッパへ縮退。 |
| C++ 専用 CLI | `py2cpp.py` | `--single-file/--multi-file`, `--header-output`, `--emit-runtime-cpp`, `--output-dir`, C++/EAST3/CppOpt 固有 option 群 | `py2x` 共通には入れず、backend option（`--lower/optimizer/emitter-option`）または `py2cpp.py` 互換ラッパに残す。 |
| Java 専用 post-process | `py2java.py` | 出力ファイル名から `class_name` を導出 | backend extension hook（packaging hook）として registry で扱う。 |

### runtime 配置差分

| 種別 | 対象 | 現状 | `py2x` で残す差分 |
| --- | --- | --- | --- |
| runtime 同梱なし | `py2cs.py` | 出力 `.cs` のみ書き出し | なし |
| JS shim 同梱 | `py2js.py`, `py2ts.py` | `write_js_runtime_shims(output_dir)` を呼び出し | `runtime_packaging_hook=js_shims` として backend registry 化 |
| 単一 runtime ファイル同梱 | `py2rs/go/java/kotlin/swift/rb/lua/scala/nim` | `py_runtime.*`（Javaは `PyRuntime.java`）を同一出力ディレクトリへコピー | `runtime_packaging_hook=single_runtime_file` として backend ごとに `source/dest` を宣言 |
| runtime 複数ファイル同梱 | `py2php.py` | `pytra/` 配下へ `py_runtime.php`, `runtime/png.php`, `runtime/gif.php` をコピー | `runtime_packaging_hook=runtime_tree_copy` として backend registry 化 |
| runtime 生成モードを持つ | `py2cpp.py` | `--emit-runtime-cpp` で runtime module から `pytra-gen` を生成 | `py2x` 初期導入では対象外（`py2cpp.py` 互換ラッパ経由を維持） |

### 共通 frontend 化で残す差分（確定）

1. 入力解決（`.py/.json -> EAST3`）、共通 guard、共通出力書き込みは `py2x` に集約する。  
2. runtime 配置は backend registry の `runtime_packaging_hook` に委譲する。  
3. C++ 固有の多量 CLI は段階移行し、初期フェーズは `py2cpp.py` 互換ラッパを維持する。  
4. Java の `class_name` 導出など backend 固有 post-process は `backend extension hook` で管理する。  

## S1-02 共通 CLI 仕様（2026-03-03）

### 基本形

```bash
python3 src/py2x.py INPUT.py --target <lang> -o OUTPUT
```

- `--target` は必須（初期対応: `cpp/rs/cs/js/ts/go/java/swift/kotlin/ruby/lua/scala/php/nim`）。
- `INPUT` は `.py` または `.json`（EAST3 JSON）を許可する。
- `-o/--output` は従来どおり明示指定を推奨（未指定時規約は wrapper 互換を踏襲）。

### 共通オプション

- `--parser-backend`（`.py` 入力時の EAST 生成 backend 選択）
- `--east-stage`（受理値は `3` のみ、`2` は fail-fast）
- `--object-dispatch-mode`（`native|type_id`）
- EAST3 optimizer 共通:
  - `--east3-opt-level`
  - `--east3-opt-pass`
  - `--dump-east3-before-opt`
  - `--dump-east3-after-opt`
  - `--dump-east3-opt-trace`

### 層別 option pass-through

- `--lower-option key=value`（複数指定可）
- `--optimizer-option key=value`（複数指定可）
- `--emitter-option key=value`（複数指定可）
- 受理した key/value は `backend registry` の schema で検証する（S1-03 で定義）。

### 互換オプション方針

- 既存 `py2*.py` は当面 thin wrapper として残し、既存 CLI を `py2x` へ変換して委譲する。
- C++ 固有大規模 CLI（`--single-file/--multi-file`、`--emit-runtime-cpp` 等）は初期段階では wrapper 側で保持し、段階移行する。
- Java の `class_name` 導出など backend 固有 post-process は frontend 固有分岐ではなく backend hook へ移管する。

### fail-fast 規約

1. `--target` 未指定・未知 target は即時エラー。  
2. `--east-stage 2` は即時エラー（互換モード廃止）。  
3. 層別 option の書式不正（`key=value` でない）は即時エラー。  
4. backend schema にない key、型不一致値は即時エラー。  
5. `.json` 入力で parser 系 option が指定された場合は警告ではなく無視不可エラー（明示的に不整合を止める）。  

決定ログ:
- 2026-03-02: ユーザー指示により、言語別 frontend の重複を解消するため `py2x.py` 一本化計画を P2 として起票。
- 2026-03-02: option 指定は層別 pass-through（`--lower-option`, `--optimizer-option`, `--emitter-option`）を正とし、backend schema 検証の fail-fast を採用。
- 2026-03-03: [ID: P2-PY2X-UNIFIED-FRONTEND-01-S1-01] `py2*.py` の CLI/runtime 配置差分を棚卸しし、共通化で残す差分を「runtime hook」「backend post-process」「C++互換ラッパ維持」に分類して確定した。
- 2026-03-03: [ID: P2-PY2X-UNIFIED-FRONTEND-01-S1-02] `py2x` 共通 CLI 仕様（基本形、共通オプション、層別 pass-through、互換方針、fail-fast 規約）を確定した。
