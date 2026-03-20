<a href="../../en/language/backend-test-matrix.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# Backend Test Matrix

このページは、backend ごとの `test/unit/toolchain/emit/<backend>/` suite が現在どこまで green かを可視化する publish target です。

## 目的

- 「support claim」ではなく、実際の backend-owned test suite の通過状況を 2 次元で見る。
- `docs/ja/language/backend-parity-matrix.md` の test 版として、実装 claim と test 実測を分けて公開する。
- backend ごとの smoke / shared smoke / backend directory 全体 discover の差を、同じ表で把握する。
- このページは backend-owned suite health の publish target であり、[backend-coverage-matrix.md](./backend-coverage-matrix.md) の代替ではありません。
- bundle-based coverage seed と ownership は [backend-coverage-matrix.md](./backend-coverage-matrix.md) を参照する。

## Maintenance Rule

- このページは [`tools/export_backend_test_matrix.py`](/workspace/Pytra/tools/export_backend_test_matrix.py) で更新する。
- 対象は `test/unit/toolchain/emit/<backend>/` 配下の backend-owned suite と、`test/unit/toolchain/emit/test_py2starred_smoke.py` 相当の shared smoke とする。
- 状態は `🟩 PASS` / `🟥 FAIL` / `🟨 TM` (`toolchain_missing`) / `🟪 TO` (`timeout`) の 4 種で表示する。
- GitHub の Markdown render では `<style>` や inline style が sanitization で落ちるため、このページは CSS なしで読める plain table を使う。

<!-- BEGIN BACKEND TEST MATRIX TABLE -->

| suite | cpp | rs | cs | js | ts | go | java | swift | kt | rb | lua | scala | php | nim |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Primary Smoke | 🟩 `PASS` | 🟥 `FAIL` | 🟩 `PASS` | 🟩 `PASS` | 🟩 `PASS` | 🟩 `PASS` | 🟥 `FAIL` | 🟩 `PASS` | 🟩 `PASS` | 🟥 `FAIL` | 🟩 `PASS` | 🟥 `FAIL` | 🟩 `PASS` | 🟩 `PASS` |
| Backend Dir Discover | 🟪 `TO` | 🟥 `FAIL` | 🟩 `PASS` | 🟩 `PASS` | 🟩 `PASS` | 🟩 `PASS` | 🟥 `FAIL` | 🟩 `PASS` | 🟩 `PASS` | 🟥 `FAIL` | 🟩 `PASS` | 🟥 `FAIL` | 🟩 `PASS` | 🟩 `PASS` |
| Shared Starred Smoke | 🟩 `PASS` | 🟩 `PASS` | 🟩 `PASS` | 🟩 `PASS` | 🟩 `PASS` | 🟩 `PASS` | 🟩 `PASS` | 🟩 `PASS` | 🟩 `PASS` | 🟩 `PASS` | 🟩 `PASS` | 🟩 `PASS` | 🟩 `PASS` | 🟩 `PASS` |

<!-- END BACKEND TEST MATRIX TABLE -->

<!-- BEGIN BACKEND TEST MATRIX DETAILS -->
## Backend Summary

| backend | passing modules | failing modules | toolchain missing | timeout | total modules |
| --- | ---: | ---: | ---: | ---: | ---: |
| cpp | 12 | 5 | 0 | 1 | 18 |
| rs | 0 | 1 | 0 | 0 | 1 |
| cs | 1 | 0 | 0 | 0 | 1 |
| js | 1 | 0 | 0 | 0 | 1 |
| ts | 1 | 0 | 0 | 0 | 1 |
| go | 1 | 0 | 0 | 0 | 1 |
| java | 0 | 1 | 0 | 0 | 1 |
| swift | 1 | 0 | 0 | 0 | 1 |
| kt | 1 | 0 | 0 | 0 | 1 |
| rb | 0 | 1 | 0 | 0 | 1 |
| lua | 1 | 0 | 0 | 0 | 1 |
| scala | 1 | 1 | 0 | 0 | 2 |
| php | 1 | 0 | 0 | 0 | 1 |
| nim | 1 | 0 | 0 | 0 | 1 |

## 実行詳細

### Summary Suites

| backend | suite | status | sec | detail |
| --- | --- | --- | ---: | --- |
| cpp | Primary Smoke | pass | 3.3 | test_py2cpp_smoke.py |
| cpp | Backend Dir Discover | timeout | 300.0 | timeout after 300s |
| cpp | Shared Starred Smoke | pass | 1.9 | test_py2starred_smoke.py equivalent |
| rs | Primary Smoke | fail | 6.5 | RuntimeError: raw EAST3 $.body[1].meta.lifetime_analysis.def_use.defs.meta must be an object: any_dict_items |
| rs | Backend Dir Discover | fail | 7.0 | RuntimeError: raw EAST3 $.body[1].meta.lifetime_analysis.def_use.defs.meta must be an object: any_dict_items |
| rs | Shared Starred Smoke | pass | 1.4 | test_py2starred_smoke.py equivalent |
| cs | Primary Smoke | pass | 6.6 | test_py2cs_smoke.py |
| cs | Backend Dir Discover | pass | 6.9 | all backend-owned modules |
| cs | Shared Starred Smoke | pass | 1.4 | test_py2starred_smoke.py equivalent |
| js | Primary Smoke | pass | 8.7 | test_py2js_smoke.py |
| js | Backend Dir Discover | pass | 8.3 | all backend-owned modules |
| js | Shared Starred Smoke | pass | 1.1 | test_py2starred_smoke.py equivalent |
| ts | Primary Smoke | pass | 8.3 | test_py2ts_smoke.py |
| ts | Backend Dir Discover | pass | 8.2 | all backend-owned modules |
| ts | Shared Starred Smoke | pass | 1.1 | test_py2starred_smoke.py equivalent |
| go | Primary Smoke | pass | 3.5 | test_py2go_smoke.py |
| go | Backend Dir Discover | pass | 3.4 | all backend-owned modules |
| go | Shared Starred Smoke | pass | 1.3 | test_py2starred_smoke.py equivalent |
| java | Primary Smoke | fail | 4.2 | RuntimeError: raw EAST3 $.body[4].meta.lifetime_analysis.def_use.defs.kind must be non-empty string: 07_game_of_life_loop |
| java | Backend Dir Discover | fail | 4.1 | RuntimeError: raw EAST3 $.body[4].meta.lifetime_analysis.def_use.defs.kind must be non-empty string: 07_game_of_life_loop |
| java | Shared Starred Smoke | pass | 1.2 | test_py2starred_smoke.py equivalent |
| swift | Primary Smoke | pass | 5.3 | test_py2swift_smoke.py |
| swift | Backend Dir Discover | pass | 3.7 | all backend-owned modules |
| swift | Shared Starred Smoke | pass | 1.2 | test_py2starred_smoke.py equivalent |
| kt | Primary Smoke | pass | 7.4 | test_py2kotlin_smoke.py |
| kt | Backend Dir Discover | pass | 6.7 | all backend-owned modules |
| kt | Shared Starred Smoke | pass | 1.3 | test_py2starred_smoke.py equivalent |
| rb | Primary Smoke | fail | 5.7 | RuntimeError: raw EAST3 $.body[4].meta.lifetime_analysis.def_use.defs.kind must be non-empty string: 07_game_of_life_loop |
| rb | Backend Dir Discover | fail | 5.2 | RuntimeError: raw EAST3 $.body[4].meta.lifetime_analysis.def_use.defs.kind must be non-empty string: 07_game_of_life_loop |
| rb | Shared Starred Smoke | pass | 1.1 | test_py2starred_smoke.py equivalent |
| lua | Primary Smoke | pass | 3.6 | test_py2lua_smoke.py |
| lua | Backend Dir Discover | pass | 3.6 | all backend-owned modules |
| lua | Shared Starred Smoke | pass | 1.2 | test_py2starred_smoke.py equivalent |
| scala | Primary Smoke | fail | 3.5 | RuntimeError: raw EAST3 $.body[5].body[5].arg_index.kind must be non-empty string: 18_mini_language_interpreter |
| scala | Backend Dir Discover | fail | 3.7 | RuntimeError: raw EAST3 $.body[5].body[5].arg_index.kind must be non-empty string: 18_mini_language_interpreter |
| scala | Shared Starred Smoke | pass | 1.4 | test_py2starred_smoke.py equivalent |
| php | Primary Smoke | pass | 3.7 | test_py2php_smoke.py |
| php | Backend Dir Discover | pass | 3.7 | all backend-owned modules |
| php | Shared Starred Smoke | pass | 1.1 | test_py2starred_smoke.py equivalent |
| nim | Primary Smoke | pass | 3.9 | test_py2nim_smoke.py |
| nim | Backend Dir Discover | pass | 3.8 | all backend-owned modules |
| nim | Shared Starred Smoke | pass | 1.0 | test_py2starred_smoke.py equivalent |

### Module Detail

| backend | module | status | sec | detail |
| --- | --- | --- | ---: | --- |
| cpp | `cpp/test_check_microgpt_original_py2cpp_regression.py` | pass | 0.4 | test_check_microgpt_original_py2cpp_regression.py |
| cpp | `cpp/test_cpp_hooks.py` | pass | 0.9 | test_cpp_hooks.py |
| cpp | `cpp/test_cpp_non_escape_bridge.py` | pass | 1.0 | test_cpp_non_escape_bridge.py |
| cpp | `cpp/test_cpp_optimizer.py` | pass | 1.7 | test_cpp_optimizer.py |
| cpp | `cpp/test_cpp_optimizer_cli.py` | pass | 3.1 | test_cpp_optimizer_cli.py |
| cpp | `cpp/test_cpp_program_writer.py` | pass | 0.7 | test_cpp_program_writer.py |
| cpp | `cpp/test_cpp_runtime_boxing.py` | pass | 2.8 | test_cpp_runtime_boxing.py |
| cpp | `cpp/test_cpp_runtime_iterable.py` | fail | 16.9 | AssertionError: -6 != 0 : runtime_iterable.out: /tmp/tmppk8i_sjl/runtime_iterable.cpp:163: int main(): Assertion `has_a && has_b' failed. |
| cpp | `cpp/test_cpp_runtime_symbol_index_integration.py` | pass | 2.4 | test_cpp_runtime_symbol_index_integration.py |
| cpp | `cpp/test_cpp_runtime_type_id.py` | pass | 9.4 | test_cpp_runtime_type_id.py |
| cpp | `cpp/test_cpp_type.py` | pass | 1.4 | test_cpp_type.py |
| cpp | `cpp/test_east3_cpp_bridge.py` | fail | 4.3 | AssertionError: 'xs.size()' != 'py_len(xs)' |
| cpp | `cpp/test_noncpp_east3_contract_guard.py` | fail | 3.1 | AssertionError: 'unsupported homogeneous tuple lane: tuple[int64, ...]' not found in '__PYTRA_USER_ERROR__/unsupported_syntax/Rust backend does not support homogeneous tuple ellipsis TypeExpr yet\n$.body[0].decl_type_expr: tuple[int64,...]\nunsupported homogeneous tuple lane: tuple[int64,...]\nadditional homogeneous tuple carriers: 3\nRepresentative tuple[T, ...] rollout is implemented only in the C++ backend right now.' |
| cpp | `cpp/test_py2cpp_codegen_issues.py` | fail | 8.4 | RuntimeError: raw EAST3 $.body[5].body[5].arg_index.kind must be non-empty string: 18_mini_language_interpreter |
| cpp | `cpp/test_py2cpp_east1_build_bridge.py` | pass | 1.7 | test_py2cpp_east1_build_bridge.py |
| cpp | `cpp/test_py2cpp_features.py` | timeout | 300.0 | timeout after 300s |
| cpp | `cpp/test_py2cpp_list_pyobj_model.py` | fail | 14.0 | RuntimeError: raw EAST3 $.body[5].body[5].arg_index.kind must be non-empty string: 18_mini_language_interpreter |
| cpp | `cpp/test_py2cpp_smoke.py` | pass | 3.9 | test_py2cpp_smoke.py |
| rs | `rs/test_py2rs_smoke.py` | fail | 8.3 | RuntimeError: raw EAST3 $.body[1].meta.lifetime_analysis.def_use.defs.meta must be an object: any_dict_items |
| cs | `cs/test_py2cs_smoke.py` | pass | 7.9 | test_py2cs_smoke.py |
| js | `js/test_py2js_smoke.py` | pass | 8.9 | test_py2js_smoke.py |
| ts | `ts/test_py2ts_smoke.py` | pass | 9.3 | test_py2ts_smoke.py |
| go | `go/test_py2go_smoke.py` | pass | 3.6 | test_py2go_smoke.py |
| java | `java/test_py2java_smoke.py` | fail | 4.8 | RuntimeError: raw EAST3 $.body[4].meta.lifetime_analysis.def_use.defs.kind must be non-empty string: 07_game_of_life_loop |
| swift | `swift/test_py2swift_smoke.py` | pass | 4.1 | test_py2swift_smoke.py |
| kt | `kotlin/test_py2kotlin_smoke.py` | pass | 7.2 | test_py2kotlin_smoke.py |
| rb | `rb/test_py2rb_smoke.py` | fail | 5.8 | RuntimeError: raw EAST3 $.body[4].meta.lifetime_analysis.def_use.defs.kind must be non-empty string: 07_game_of_life_loop |
| lua | `lua/test_py2lua_smoke.py` | pass | 3.4 | test_py2lua_smoke.py |
| scala | `scala/test_check_py2scala_transpile.py` | pass | 0.4 | test_check_py2scala_transpile.py |
| scala | `scala/test_py2scala_smoke.py` | fail | 3.6 | RuntimeError: raw EAST3 $.body[5].body[5].arg_index.kind must be non-empty string: 18_mini_language_interpreter |
| php | `php/test_py2php_smoke.py` | pass | 3.8 | test_py2php_smoke.py |
| nim | `nim/test_py2nim_smoke.py` | pass | 3.8 | test_py2nim_smoke.py |

## Scope

- overview matrix は `Primary Smoke` / `Backend Dir Discover` / `Shared Starred Smoke` の 3 行です。
- `Module Detail` は `test/unit/toolchain/emit/<backend>/test_*.py` を 1 module ずつ実行した結果です。
- `Shared Starred Smoke` は `test/unit/toolchain/emit/test_py2starred_smoke.py` と同じ fixture/assertion を backend ごとに再実行しています。
- `test/unit/toolchain/emit/` 直下の support helper (`*_support.py`) は実行対象に含めません。
<!-- END BACKEND TEST MATRIX DETAILS -->
