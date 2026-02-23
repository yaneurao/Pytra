# P0 type_id 継承判定・isinstance 統一（最優先）

ID: `TG-P0-TYPEID-ISINSTANCE`

## 関連 TODO

- `docs-jp/todo.md` の `ID: P0-TID-01`（`P0-TID-01-S1` 〜 `P0-TID-01-S4`）
- `docs-jp/todo.md` の `ID: P0-TID-02`（`P0-TID-02-S1` 〜 `P0-TID-02-S4`）

## 背景

- 現状の `isinstance` は target ごとに部分実装で、C++ は built-in 判定の組み合わせ、JS/TS は `pyTypeId` があっても継承判定 API が不足している。
- その結果、個別ケースのハードコード（`py_is_*` 分岐、言語別特例）が増えやすく、拡張時の保守コストが高い。
- ユーザー定義型・派生関係を跨ぐ共通判定基盤がないと、全言語 selfhost の足場が弱い。

## 目的

- `type_id` を使った `isinstance`/派生判定の共通契約を runtime と codegen で統一する。
- target 固有の場当たり分岐を縮退し、共通 API へ寄せる。
- `Any/object` 境界の型判定を再現可能・拡張可能な実装へ移行する。

## 非対象

- Python 完全互換（`abc` や metaclass を含む全型システム）を一度に達成すること。
- 既存全 runtime API の一括刷新。

## サブタスク実行順（todo 同期）

1. `P0-TID-01`（type_id 判定 API 統一）
   - `P0-TID-01-S1`: `spec-type_id` / `spec-boxing` / `spec-iterable` 間で `isinstance` 契約を整合させる。
   - `P0-TID-01-S2`: C++ runtime に `py_isinstance` / `py_is_subtype` を実装し、既存 call site を置換する。
   - `P0-TID-01-S3`: JS/TS runtime に同等 API を実装し、dispatch オプション方針と整合させる。
   - `P0-TID-01-S4`: 各 emitter の `isinstance` lower を runtime API 経由へ統一し、直書き分岐を縮退する。
2. `P0-TID-02`（pure Python built_in 正本化）
   - `P0-TID-02-S1`: `src/pytra/built_in/` の配置・命名・生成対象ルールを確定する。
   - `P0-TID-02-S2`: `isinstance` / `issubclass` / `type_id` を pure Python 実装へ移管する。
   - `P0-TID-02-S3`: `py2cpp.py --emit-runtime-cpp` で `src/pytra/built_in/*.py` から C++ runtime built_in 生成を可能にする。
   - `P0-TID-02-S4`: C++ 手書き built_in 実装を最小ブート層（GC/ABI 等）へ縮退する。

## `P0-TID-02-S1` で確定したルール

- 正本配置: target 非依存 built-in 意味論は `src/pytra/built_in/*.py` に置く。
- 命名: `snake_case.py` を基本とし、`_impl` 接尾辞は target 側手書き層専用として予約する。
- 生成対象: `src/pytra/built_in/<name>.py` は将来 `src/runtime/<lang>/pytra/built_in/<name>.*` へ生成する。
- 境界: GC/ABI など低レベル処理だけを `src/runtime/<lang>/pytra-core/built_in/` に残し、意味論は正本層へ寄せる。

## `P0-TID-02-S4` 分割（重複解消）

- `P0-TID-02-S4-S1`: `py_runtime.h` と `pytra-gen/built_in/type_id.*` の重複シンボルを棚卸しする。
- `P0-TID-02-S4-S2`: 手書き層に残す最小ブート責務（GC/ABI/`PyObj` 基盤）と生成層へ移す `type_id` 判定責務を確定し、移行パッチを作成する。
- `P0-TID-02-S4-S3`: 参照先を生成層優先へ切り替え、重複シンボルを削除したうえで C++ 回帰を通す。

`S4-S2` の責務境界（確定）:
- `py_runtime.h`（手書き）: GC/ABI、`PyObj` ベース、`make_object` 系と既存公開 API 入口（互換維持）。
- `pytra-gen/built_in/type_id.*`（生成）: `type_id` の registry/subtype 意味論（`py_tid_*`）正本。
- `S4-S3` で `py_runtime.h` 公開 API (`py_is_subtype` など) から `py_tid_*` へ段階委譲し、重複実装を削除する。

## 受け入れ基準

- `isinstance(x, T)` が `type_id` ベースでユーザー定義型/派生型まで判定できる。
- `type_id` モードで C++ と JS/TS の判定結果が一致する。
- `py2cpp.py` の `isinstance` 特例分岐が縮退し、runtime API 経由へ集約される。
- 既存 selfhost/transpile 導線で致命回帰がない。

## 決定ログ

- 2026-02-23: 「場当たり分岐を増やさないため、`type_id` 派生判定を最優先で進める」方針を確定し、`P0-TID-01` を追加。
- 2026-02-23: Phase 1 として C++/JS/TS runtime に共通 API（`py_is_subtype` / `py_isinstance` 系）を導入し、`py2cpp` の `isinstance` lower は built-in 判定関数直呼びから `py_isinstance(..., <type_id>)` へ移行する。C++ の GC 管理クラスには `PYTRA_TYPE_ID` と constructor 内 `set_type_id(...)` を付与する。
- 2026-02-23: `py2cpp` の class storage hint 伝播は「base->child」だけでなく「ref child->base」も含める。これにより `ref` 子クラスを持つ親クラスでも `PYTRA_TYPE_ID` が定義され、`isinstance(x, Base)` の lower を `py_isinstance(x, Base::PYTRA_TYPE_ID)` で統一できる。
- 2026-02-23: `py2cpp` の `isinstance` lower を tuple 指定（`isinstance(x, (T1, T2, ...))`）まで拡張し、各要素を `py_isinstance(..., <type_id>)` の OR 合成へ統一した。`object` は `PYTRA_TID_OBJECT` へ map し、`test/unit/test_py2cpp_codegen_issues.py` に tuple 回帰を追加。`python3 test/unit/test_py2cpp_codegen_issues.py Py2CppCodegenIssueTest.test_isinstance_builtin_lowers_to_type_id_runtime_api Py2CppCodegenIssueTest.test_isinstance_tuple_lowers_to_or_of_type_id_checks Py2CppCodegenIssueTest.test_gc_class_emits_type_id_and_isinstance_uses_runtime_api`、`python3 tools/check_py2cpp_transpile.py`（`checked=129 ok=129 fail=0 skipped=6`）、`python3 tools/build_selfhost.py`（成功）で回帰なしを確認した。
- 2026-02-23: `hooks/js` emitter（`py2js` / `py2ts` preview 共通）でも `isinstance` を `pyIsInstance(..., <type_id>)` へ移行し、class へ `PYTRA_TYPE_ID`（`pyRegisterClassType`）と constructor 内 `this[PYTRA_TYPE_ID]` を導入する。dict literal は `PY_TYPE_MAP` tag を付け、`isinstance(x, dict)` 判定を type_id 経路へ寄せる。
- 2026-02-23: `hooks/js` emitter の `isinstance` lower を tuple 指定（`isinstance(x, (T1, T2, ...))`）まで拡張し、各要素を `pyIsInstance(..., <type_id>)` の OR 合成へ統一した。`object` は `PY_TYPE_OBJECT` へ map し、`test/unit/test_py2js_smoke.py` / `test/unit/test_py2ts_smoke.py` に tuple 回帰を追加して `python3 tools/check_py2js_transpile.py` / `python3 tools/check_py2ts_transpile.py`（ともに `checked=129 ok=129 fail=0 skipped=6`）で回帰なしを確認した。
- 2026-02-23: `isinstance(x, set)` の `type_id` lower を cross-target で回帰固定した。`py2cpp` は `py_isinstance(x, PYTRA_TID_SET)`、`hooks/js`（`py2ts` preview 含む）は `pyIsInstance(x, PY_TYPE_SET)` を生成することを `test/unit/test_py2cpp_codegen_issues.py` / `test/unit/test_py2js_smoke.py` / `test/unit/test_py2ts_smoke.py` で検証し、各 transpile チェックで回帰なしを確認した。
- 2026-02-23: `hooks/cs` emitter では runtime `type_id` 導入前の段階対応として、`isinstance(x, T)` を C# の `is` 判定へ lower する。まず builtin（`int/float/bool/str/list/dict`）と user class を対象にし、`isinstance(...)` 生呼びを段階縮退する。
- 2026-02-23: `hooks/rs` emitter でも `isinstance` 生呼びを縮退し、`Any/object` は `PyAny` への `matches!`（`Int/Float/Bool/Str/List/Dict`）へ、静的型（builtin/class）は `get_expr_type` と `ClassDef.base` 継承表ベースで `true/false` へ lower する。`test/unit/test_py2rs_smoke.py` に `Any`/builtin/class 継承の回帰を追加し、`python3 test/unit/test_py2rs_smoke.py` と `python3 tools/check_py2rs_transpile.py` で回帰なしを確認した。
- 2026-02-23: `hooks/cs` / `hooks/rs` の `isinstance(..., object)` を追加実装した。C# は `(x is object)`、Rust は `true` へ lower し、target 間で `object` 判定の意味を揃えた。`test/unit/test_py2cs_smoke.py` / `test/unit/test_py2rs_smoke.py` に回帰を追加し、`python3 tools/check_py2cs_transpile.py` / `python3 tools/check_py2rs_transpile.py`（ともに `checked=129 ok=129 fail=0 skipped=6`）で回帰なしを確認した。
- 2026-02-23: `hooks/cs` / `hooks/rs` の tuple 指定 `isinstance(x, (T1, T2, ...))` lower を回帰テストで固定した。C# は OR 連結された `is` 判定（`int/Base/dict/object`）を、Rust は `Any` に対する `matches!` OR 連結（`Int`/`Dict`）を検証するテストを追加し、`python3 test/unit/test_py2cs_smoke.py`（9件成功）、`python3 test/unit/test_py2rs_smoke.py`（16件成功）、`python3 tools/check_py2cs_transpile.py` / `python3 tools/check_py2rs_transpile.py`（ともに `checked=129 ok=129 fail=0 skipped=6`）で回帰なしを確認した。
- 2026-02-23: `hooks/cs` / `hooks/rs` の `isinstance(x, set)` lower を追加した。C# は `System.Collections.ISet` への `is` 判定へ、Rust は `Any` 経路で `matches!(x, PyAny::Set(_))` へ lower する。Rust `PyAny` には `Set(Vec<PyAny>)` variant と helper（truthy/string）分岐を追加し、`test/unit/test_py2cs_smoke.py` / `test/unit/test_py2rs_smoke.py` の set 回帰、`python3 tools/check_py2cs_transpile.py` / `python3 tools/check_py2rs_transpile.py`（ともに `checked=129 ok=129 fail=0 skipped=6`）で回帰なしを確認した。
- 2026-02-23: docs-jp/todo.md の P0-TID-01 / P0-TID-02 を -S* 子タスクへ分割したため、本 plan に同一粒度の実行順を追記した。
- 2026-02-23: `P0-TID-01-S1` として `docs-jp/spec/spec-type_id.md` / `docs-jp/spec/spec-boxing.md` / `docs-jp/spec/spec-iterable.md` を整合し、`--object-dispatch-mode` の一括切替対象（`isinstance`・boxing・iterable・`bool/len/str`）と `py_is_subtype` / `py_isinstance` / `py_issubclass` 契約を統一明文化した。
- 2026-02-23: `P0-TID-01-S2` を完了。C++ runtime（`src/runtime/cpp/pytra-core/built_in/py_runtime.h`）の `py_is_subtype` / `py_issubclass` / `py_isinstance` 実装と `py2cpp` lower 経路の統一を確認し、`python3 test/unit/test_py2cpp_codegen_issues.py`（41件成功）で回帰なしを確認した。
- 2026-02-23: `P0-TID-01-S3` を完了。JS/TS runtime の `pyIsSubtype` / `pyIsInstance` と class `type_id` 登録（`pyRegisterClassType`）運用を確認し、`python3 test/unit/test_js_ts_runtime_dispatch.py`（3件成功）、`python3 test/unit/test_py2js_smoke.py`（10件成功）、`python3 test/unit/test_py2ts_smoke.py`（8件成功）で回帰なしを確認した。
- 2026-02-23: `P0-TID-01-S4` を完了。emitter 側 `isinstance` lower の runtime API 経由統一（C++/JS/TS/C#/Rust）を確認し、`python3 test/unit/test_py2cs_smoke.py`（10件成功）、`python3 test/unit/test_py2rs_smoke.py`（18件成功）、`python3 tools/check_py2cpp_transpile.py` / `python3 tools/check_py2js_transpile.py` / `python3 tools/check_py2ts_transpile.py` / `python3 tools/check_py2cs_transpile.py` / `python3 tools/check_py2rs_transpile.py`（いずれも `checked=131 ok=131 fail=0 skipped=6`）で回帰なしを確認した。
- 2026-02-23: `P0-TID-02-S1` を完了。`src/pytra/built_in/` を新設し、`__init__.py` と `README.md` で配置・命名・生成対象ルール（正本層 / 生成先 / 低レベル層境界）を確定した。
- 2026-02-23: `P0-TID-02-S2` を完了。`src/pytra/built_in/type_id.py` へ `py_tid_register_class_type` / `py_tid_is_subtype` / `py_tid_issubclass` / `py_tid_runtime_type_id` / `py_tid_isinstance` の pure Python 実装を移管し、`python3 test/unit/test_pytra_built_in_type_id.py`（4件成功）で回帰なしを確認した。
- 2026-02-23: `P0-TID-02-S3` を完了。`py2cpp.py --emit-runtime-cpp` の対象に `src/pytra/built_in/` を追加し、`python3 src/py2cpp.py src/pytra/built_in/type_id.py --emit-runtime-cpp` で `src/runtime/cpp/pytra-gen/built_in/type_id.{h,cpp}` と互換フォワーダー `src/runtime/cpp/pytra/built_in/type_id.{h,cpp}` が生成されることを確認した。回帰として `python3 test/unit/test_py2cpp_features.py Py2CppFeatureTest.test_runtime_module_tail_and_namespace_support_compiler_tree`、`python3 tools/check_py2cpp_transpile.py`（`checked=131 ok=131 fail=0 skipped=6`）を実行した。
- 2026-02-23: `P0-TID-02-S4-S1` を完了。`src/runtime/cpp/pytra-core/built_in/py_runtime.h` と `src/runtime/cpp/pytra-gen/built_in/type_id.*` を棚卸しし、重複対象を `PYTRA_TID_*`、`py_register_class_type`、`py_is_subtype`、`py_issubclass`、`py_runtime_type_id`、`py_isinstance` と確定した。移行作業を `S4-S1`〜`S4-S3` へ分割した。
- 2026-02-23: `P0-TID-02-S4-S2` を完了。`src/pytra/built_in/type_id.py` を `PYB_TID_*` / `py_tid_*` 命名へ再設計して手書き API と衝突しない生成形へ移行し、`python3 src/py2cpp.py src/pytra/built_in/type_id.py --emit-runtime-cpp` 後の `src/runtime/cpp/pytra-gen/built_in/type_id.cpp` が `g++ -std=c++17 -I src -I src/runtime/cpp -fsyntax-only` を通ることを確認した。
