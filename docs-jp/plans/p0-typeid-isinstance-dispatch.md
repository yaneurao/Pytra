# P0 type_id 継承判定・isinstance 統一（最優先）

ID: `TG-P0-TYPEID-ISINSTANCE`

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

## 実施項目

1. 共通判定 API を定義する（例: `py_isinstance(obj, type_id)` / `py_is_subtype(actual, expected)`）。
2. C++ runtime で `type_id` と派生関係テーブル（または同等機構）を実装する。
3. JS/TS runtime で `type_id` モード時の同等 API を実装し、継承判定を可能にする。
4. `py2cpp`（必要に応じて他言語 emitter）で `isinstance` lower を新 API 経由へ切り替える。
5. built-in 直書き分岐を段階縮退し、回帰テストで固定する。

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
- 2026-02-23: `hooks/cs` emitter では runtime `type_id` 導入前の段階対応として、`isinstance(x, T)` を C# の `is` 判定へ lower する。まず builtin（`int/float/bool/str/list/dict`）と user class を対象にし、`isinstance(...)` 生呼びを段階縮退する。
- 2026-02-23: `hooks/rs` emitter でも `isinstance` 生呼びを縮退し、`Any/object` は `PyAny` への `matches!`（`Int/Float/Bool/Str/List/Dict`）へ、静的型（builtin/class）は `get_expr_type` と `ClassDef.base` 継承表ベースで `true/false` へ lower する。`test/unit/test_py2rs_smoke.py` に `Any`/builtin/class 継承の回帰を追加し、`python3 test/unit/test_py2rs_smoke.py` と `python3 tools/check_py2rs_transpile.py` で回帰なしを確認した。
- 2026-02-23: `hooks/cs` / `hooks/rs` の `isinstance(..., object)` を追加実装した。C# は `(x is object)`、Rust は `true` へ lower し、target 間で `object` 判定の意味を揃えた。`test/unit/test_py2cs_smoke.py` / `test/unit/test_py2rs_smoke.py` に回帰を追加し、`python3 tools/check_py2cs_transpile.py` / `python3 tools/check_py2rs_transpile.py`（ともに `checked=129 ok=129 fail=0 skipped=6`）で回帰なしを確認した。
- 2026-02-23: `hooks/cs` / `hooks/rs` の tuple 指定 `isinstance(x, (T1, T2, ...))` lower を回帰テストで固定した。C# は OR 連結された `is` 判定（`int/Base/dict/object`）を、Rust は `Any` に対する `matches!` OR 連結（`Int`/`Dict`）を検証するテストを追加し、`python3 test/unit/test_py2cs_smoke.py`（9件成功）、`python3 test/unit/test_py2rs_smoke.py`（16件成功）、`python3 tools/check_py2cs_transpile.py` / `python3 tools/check_py2rs_transpile.py`（ともに `checked=129 ok=129 fail=0 skipped=6`）で回帰なしを確認した。
