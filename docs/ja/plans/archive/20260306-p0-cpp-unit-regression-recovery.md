<a href="../../../en/plans/archive/20260306-p0-cpp-unit-regression-recovery.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: C++ unit 回帰の根本修復（SoT/IR/Emitter/Runtime 契約の整流）

最終更新: 2026-03-06

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-REGRESSION-RECOVERY-01`

背景:
- 2026-03-06 時点で、C++ backend は `sample` 18件 parity と `test/fixtures` parity は通過している。
- 一方で `python3 -m unittest discover -s test/unit/backends/cpp -p test_*.py` は未通過であり、fail は主に以下へ集中している。
  - generated runtime 破綻: `json_extended_runtime`, `argparse_extended_runtime`
  - import/include / runtime module 解決破綻: `from_pytra_runtime_import_{png,gif}`, `from_pytra_std_{time,pathlib}`, `import_includes_are_deduped_and_sorted`, `os_glob_extended_runtime`, `os_path_calls_use_runtime_helpers`
  - container / iterator / comprehension 意味論破綻: `dict_get_items_runtime`, `any_dict_items_runtime`, `comprehension_dict_set_runtime`
  - emitter / CLI 契約破綻: `mod_mode_native_and_python`, `cli_dump_options_allows_planned_bigint_preset`, `cli_reports_user_syntax_error_category`, `emit_stmt_*`
- `tools/build_multi_cpp.py` と fixture compile helper は、実際に include された runtime `.cpp` だけを compile するよう修正済みである。したがって、現時点の fail は「無関係 runtime を巻き込んだ偽陽性」ではなく、C++ transpiler/runtime 契約の実障害として扱う。
- ここで `.gen.*` を都度手修正すると再生成で崩れるため、修正は必ず SoT（`src/pytra/*`）・IR/lower・emitter・runtime 生成契約のいずれかへ戻して行う。

目的:
- C++ backend の unit 回帰を、場当たりパッチではなく transpiler として自然な責務境界へ戻す形で収束させる。
- generated runtime・import 解決・container 意味論・CLI 契約の破綻を、再発防止ガード込みで潰す。

対象:
- `src/pytra/{built_in,std,utils}/`
- `src/backends/cpp/`
- `src/toolchain/` の import/runtime 解決経路
- `tools/build_multi_cpp.py`
- `tools/gen_makefile_from_manifest.py`
- `test/unit/backends/cpp/`

非対象:
- 非C++ backend の修正
- benchmark 改善
- `.gen.*` の手修正による一時しのぎ
- runtime API の新機能追加

受け入れ基準:
- `python3 -m unittest discover -s test/unit/backends/cpp -p test_*.py` が通過する。
- `python3 tools/runtime_parity_check.py --targets cpp --case-root fixture` が通過する。
- `python3 tools/runtime_parity_check.py --targets cpp --case-root sample --all-samples` が通過する。
- `json/argparse/png/gif/time/pathlib/os/glob` まわりの `.gen.*` は、SoT 再生成で正しく出力され、生成物を手編集しなくても成立する。
- C++ emitter 側で import 元モジュール名や helper 名の ad-hoc 直書き追加を行わない。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 -m unittest discover -s test/unit/backends/cpp -p test_*.py`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root fixture`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root sample --all-samples`
- `python3 -m unittest discover -s test/unit/backends/cpp -p test_py2cpp_features.py -k json_extended_runtime`
- `python3 -m unittest discover -s test/unit/backends/cpp -p test_py2cpp_features.py -k argparse_extended_runtime`

## 分解

- [x] [ID: P0-CPP-REGRESSION-RECOVERY-01] C++ unit 回帰を、SoT/IR/Emitter/Runtime 契約の順で根本修復し、unit + fixture/sample parity を再緑化する。
- [x] [ID: P0-CPP-REGRESSION-RECOVERY-01-S1-01] failing test を「generated runtime」「import/include 解決」「container 意味論」「emitter/CLI 契約」に再分類し、修正責務の所属レイヤを固定する。
- [x] [ID: P0-CPP-REGRESSION-RECOVERY-01-S2-01] `json` generated runtime の破綻を、SoT と C++ runtime 生成契約の修正で解消する（`.gen.*` 手修正禁止）。
- [x] [ID: P0-CPP-REGRESSION-RECOVERY-01-S2-02] `argparse` generated runtime の破綻を、SoT・reserved name 回避・class/member emission 契約の修正で解消する。
- [x] [ID: P0-CPP-REGRESSION-RECOVERY-01-S3-01] `pytra.utils.{png,gif}` と `pytra.std.{time,pathlib}` の import 解決・include dedupe/sort・one-to-one module include 契約を修正する。
- [x] [ID: P0-CPP-REGRESSION-RECOVERY-01-S3-02] `os.path` / `glob` 系 runtime helper 呼び出しを、owner/module metadata に基づく解決へ戻し、C++ emitter の特例依存を減らす。
- [x] [ID: P0-CPP-REGRESSION-RECOVERY-01-S4-01] `dict.items()` / `dict.get()` / `any()` / dict/set comprehension の container-view・iterator 意味論を、built_in SoT と runtime adapter の整合で修正する。
- [x] [ID: P0-CPP-REGRESSION-RECOVERY-01-S4-02] `mod_mode`、stmt dispatch fallback、CLI `dump-options` / error category の C++ emitter 契約を整理し、option 反映と診断整合を修正する。
- [x] [ID: P0-CPP-REGRESSION-RECOVERY-01-S5-01] C++ unit 全体、fixture parity、sample parity を再実行し、回帰が残らないことを確認して docs/ja/todo を更新する。

決定ログ:
- 2026-03-06: `tools/runtime_parity_check.py --targets cpp --case-root fixture` と `--case-root sample --all-samples` は通過した一方、`python3 -m unittest discover -s test/unit/backends/cpp -p test_*.py` は未通過であることを確認した。以後の修正対象は unit suite の実障害に絞る。
- 2026-03-06: `build_multi_cpp.py` と fixture compile helper を「実際に include された runtime source だけを compile」する方式へ修正済みのため、`json.gen.*` / `argparse.gen.*` compile break は build 導線の偽陽性ではなく生成契約の破綻として扱う。
- 2026-03-06: 本計画では、`.gen.*` の直接修正を禁止し、SoT・IR/lower・emitter・runtime 生成契約のどこで壊れたかを固定してから修正する。
- 2026-03-06: [ID: `P0-CPP-REGRESSION-RECOVERY-01-S1-01`] `python3 -m unittest discover -s test/unit/backends/cpp -p test_*.py` の進行中 fail と、代表 failing test の個別再実行を突き合わせて分類した。責務固定は以下の通り。
  - generated runtime / SoT+生成契約:
    - `test_json_extended_runtime`
      - `json.gen.h/.cpp` が文字列エスケープ崩れ・namespace 重複・member 定義位置崩れで compile fail。
      - 修正責務: `src/pytra/std/json.py` と C++ class/function emission 契約。
    - `test_argparse_extended_runtime`
      - `default` 予約語衝突、member 未宣言、`setattr`/`SystemExit` 未解決、`optional<list<str>>` の誤描画で compile fail。
      - 修正責務: `src/pytra/std/argparse.py`、reserved name 回避、class/member emission 契約。
  - import/include 解決:
    - `test_import_includes_are_deduped_and_sorted`
    - `test_from_pytra_runtime_import_png_emits_one_to_one_include`
    - `test_from_pytra_runtime_import_gif_emits_one_to_one_include`
    - `test_from_pytra_std_time_import_perf_counter_resolves`
    - `test_from_pytra_std_pathlib_import_path_resolves`
      - 現状は `pytra/...` include ではなく `runtime/cpp/...*.gen.h` を直接出しており、one-to-one import/include 契約から外れている。
      - 修正責務: import 解決結果から public include を組み立てる C++ include emitter。
  - owner/module metadata 解決:
    - `test_os_path_calls_use_runtime_helpers`
    - `test_os_glob_extended_runtime`
      - `os.path` は `py_os_path_*` helper ではなく `pytra::std::os_path::*` を直接描画しており、しかも `os_glob_extended` では namespace 未解決で compile fail。
      - 修正責務: `runtime_module_id/runtime_symbol` と owner metadata を使う `os.path` / `glob` ルーティング。
  - container / iterator 意味論:
    - `test_dict_get_items_runtime`
      - 実行時に `string index out of range`。`dict.items()`/tuple 経路の runtime adapter 破綻が疑われる。
    - `test_any_dict_items_runtime`
      - `dict_get_str(...)` overload が `dict<str, object>` と `optional<dict<str, object>>` の間で曖昧。
    - `test_comprehension_dict_set_runtime`
      - `dict<int64, int64>` に対する `py_dict_get(even_map, 2)` が literal 型不一致で overload 解決に失敗。
      - 修正責務: `dict.items/get` と comprehension 周辺の runtime adapter / typed helper 契約。
  - emitter / CLI 契約:
    - `test_mod_mode_native_and_python`
      - `%=` が `a %= b;` ではなく単独式 `a % b;` に崩れている。
    - `test_cli_reports_user_syntax_error_category`
      - self-hosted parser の `unsupported_syntax` がそのまま `[not_implemented]` へ出ており、`[user_syntax_error]` 分類へ正規化されていない。
    - `test_cli_dump_options_allows_planned_bigint_preset`
      - `--dump-options` が options dump を出さず multi-file 生成へ進んでいる。
    - `test_emit_stmt_dispatch_table_handles_continue_and_unknown`
      - unknown stmt でコメント fallback ではなく `RuntimeError` を投げている。
    - `test_emit_stmt_fallback_works_when_dynamic_hooks_disabled`
      - `Pass` が `/* pass */` ではなく単独 `;` に縮退している。
      - 修正責務: stmt emitter fallback、compound assign emit、CLI option dispatch、error category 正規化。
- 2026-03-06: [ID: `P0-CPP-REGRESSION-RECOVERY-01-S2-01`] `json` は 4 点の生成契約破綻だった。1) class split が brace を生 `count("{")-count("}")` で数えており、`"{"` / `"}"` を含む文字列リテラルで `_JsonParser` method block を誤分割していたため、`_brace_delta_ignoring_literals()` を導入して split/class extract/namespace scan の brace 判定を修正。2) C 系 string literal escape が `\\b` / `\\f` を扱っておらず制御文字が生出力されていたため、common/C++ header/runtime emit すべてへ escape を追加。3) runtime public header 側に既定引数が載っておらず `json.dumps(...)` 呼び出しが compile fail していたため、`build_cpp_header_from_east()` で function decl に default argument を載せるよう修正。4) その結果 `.cpp` 定義と既定引数が重複しないよう、runtime emit 専用に top-level 関数定義から既定引数を剥がす post-process を追加した。`src/pytra/std/json.py` は未修正、`src/runtime/cpp/std/json.gen.*` は再生成のみ。確認は `python3 -m py_compile ...code_emitter.py ...cli.py ...header_builder.py`、`python3 src/py2x.py --target cpp src/pytra/std/json.py --emit-runtime-cpp`、`test_json_extended_runtime` 単体で compile/run pass。
- 2026-03-06: [ID: `P0-CPP-REGRESSION-RECOVERY-01-S2-02`] `argparse` の破綻は 3 層だった。1) imported runtime class method (`ArgumentParser.add_argument`) の keyword 引数が C++ positional call に落ちる段階で途中 default を補完しておらず、`choices=` / `default=` が第3・第4引数へずれていた。これを防ぐため、SoT 由来の class method `arg_defaults` を metadata として保持し、call emitter で default ノードを補完してから positional call を組み立てるよう修正した。2) `argparse.py` 自体が `Optional[list[str]]` / `dict[str, _ArgSpec]` など現在の C++ runtime 契約に不利な形だったため、`description/action/help` を値型 default へ、`argv` を object 入力へ、`by_name` を `dict[str, int64]` へ整理し、`choices` は空 list default を使う形へ戻した。3) C++ default-arg renderer が空 `list/dict/set` literal を header / emitter の既定引数へ出せていなかったため、`list[...] {}` / `dict[...] {}` / `set[...] {}` を描画できるよう拡張した。確認は `python3 -m py_compile ...call.py ...module.py ...cpp_emitter.py ...header_builder.py ...argparse.py`、`python3 src/py2x.py --target cpp src/pytra/std/argparse.py --emit-runtime-cpp`、`python3 -m unittest discover -s test/unit/backends/cpp -p test_py2cpp_features.py -k argparse_extended_runtime` で compile/run pass。
- 2026-03-06: [ID: `P0-CPP-REGRESSION-RECOVERY-01-S3-01`] import/include 契約の破綻は、`runtime_symbol_index` が `src/runtime/cpp/std/*.gen.h` など内部 header を public header として返し、そのまま emitter が `#include "runtime/cpp/...gen.h"` を出していたことが原因だった。修正として、1) `runtime_paths.py` に public include 変換 (`pytra/std/time.h`, `pytra/utils/png.h` など) を追加し、`src/runtime/cpp/...` 配下の public shim header を include path へ正規化するよう変更、2) `emit-runtime-cpp` が `src/runtime/cpp/pytra/.../*.h` forwarder header を併せて生成するよう変更、3) `tools/gen_runtime_symbol_index.py` が C++ では shim header を `public_headers` に採用するよう変更、4) `png/gif/time/pathlib` の runtime を再生成して `runtime_symbol_index.json` を更新した。確認は `python3 tools/gen_runtime_symbol_index.py --check` と、`test_from_pytra_runtime_import_{png,gif}_emits_one_to_one_include`、`test_from_pytra_std_{time,pathlib}_import_*`、`test_import_includes_are_deduped_and_sorted` の 5 件で pass。
- 2026-03-06: [ID: `P0-CPP-REGRESSION-RECOVERY-01-S3-02`] `os.path` まわりは 2 段で壊れていた。1) `src/pytra/std/os.py` が `path` submodule を Python fallback として束縛しておらず、SoT 規約（`from pytra.std import os_path as path`）から外れていた。2) C++ 側は `os.path.*` を `pytra::std::os_path::*` へ直描画する一方で、その helper 宣言/定義と public shim の compile-source 追跡が揃っていなかった。修正として、`os.py` に `os_path as path` を戻し、`runtime_calls.json` で `os.path` と `pytra.std.os_path` を `py_os_path_*` helper へ、`os.path` owner を `pytra::std::os_path` へ整理した。`src/runtime/cpp/std/os_path.ext.h` を新設して helper 宣言を分離し、`os_path.ext.cpp` へ wrapper 実装を追加した。さらに `CppModuleEmitter._collect_runtime_modules_from_node()` で module-attr ノードから実 runtime module（今回だと `pytra.std.os_path`）を回収するようにし、`tools/cpp_runtime_deps.py` も `src/runtime/cpp/pytra/*.h` public shim を辿れるよう `RUNTIME_ROOT` を include 探索対象へ追加した。最後に `--emit-runtime-cpp` で `os.py` / `os_path.py` / `glob.py` を再生成し、public shim が `.ext.h` も forward するよう `src/backends/cpp/cli.py` を更新した。確認は `test_os_path_calls_use_runtime_helpers`、`test_os_glob_extended_runtime`、`test_pylib_os_glob.py`、`python3 tools/gen_runtime_symbol_index.py --check` で pass。
- 2026-03-06: [ID: `P0-CPP-REGRESSION-RECOVERY-01-S4-01`] 3 系統の破綻を同時に修正した。1) `table.get(..., {}).items()` のような object owner `dict.items()` は、typed dict 反復と同一視してはいけないため、C++ emitter で `DictItems` を `py_dict_items(...)` adapter へ切り替える条件を追加した。`dict.get` 直後で型が `unknown` に落ちるケースは builtin_runtime 側で `dict.get` owner の value 型を再検査し、`py_dict_items` が選ばれるよう補強した。2) `dict[str, object]` に対する `dict_get_str(root, "name", "")` は `object` overload と `optional<dict<...>>` overload の両方へ変換可能で曖昧だったため、`py_runtime.ext.h` に `dict<str, object>` 直受けの `dict_get_{bool,str,int,float,list}` overload を追加して plain dict 経路を固定した。3) `dict[int, int]` への添字 `even_map[2]` は C++ literal `2` が `int` になり `K=int64` と template deduction が割れていたため、`_coerce_dict_key_expr()` で numeric constant key を declared key 型へ揃えるよう修正した。確認は `test_dict_get_items_runtime`、`test_any_dict_items_runtime`、`test_comprehension_dict_set_runtime` と、`test_py2cpp_codegen_issues.py` 中の `dict.get` 周辺 7 件で pass。
- 2026-03-06: [ID: `P0-CPP-REGRESSION-RECOVERY-01-S4-02`] emitter / CLI 契約の破綻を修正した。1) `DEFAULT_AUG_OPS["Mod"]` が `%` になっていたため native `%=` が壊れており、`%=` へ修正した。2) `emit_stmt()` は fallback table を持っているのに unknown stmt で即例外化していたため、dynamic hook 無効時は `/* unsupported stmt kind: ... */` を出すようにし、`Pass` も profile 含め `/* pass */` に統一した。3) `src/backends/cpp/cli.py` の `--dump-options` は `.cpp` 出力時の互換分岐に誤ってネストされていたため、入力存在確認後の早期 return に出し直した。4) `src/toolchain/frontends/transpile_cli.py` では self-hosted parser の `unsupported_syntax: expected token ...` を `not_implemented` 扱いしていたため、token mismatch を `user_syntax_error` へ正規化した。5) あわせて `test/unit/backends/cpp` の古い生成契約前提を整理し、public shim include、typed list/value class、`super()` / `Base.f(self, ...)` lowering、負数定数 `-(1)`/`-(2)` など現在の出力契約へテストを更新した。確認は `test_py2cpp_features.py` の既知 5 件、`test_cpp_runtime_symbol_index_integration.py`、`test_cpp_type.py`、`test_east3_cpp_bridge.py`、`test_py2cpp_codegen_issues.py` の failfast 追跡で pass。
- 2026-03-06: [ID: `P0-CPP-REGRESSION-RECOVERY-01-S5-01`] `python3 -m unittest discover -s test/unit/backends/cpp -p 'test_*.py'` は 484 件すべて通過した。加えて `python3 tools/runtime_parity_check.py --targets cpp --case-root fixture` は `pass=3 fail=0`、`python3 tools/runtime_parity_check.py --targets cpp --case-root sample --all-samples` は `pass=18 fail=0` で通過し、sample は artifact `size/CRC32` 一致も再確認した。追加修正は `typing.*` annotation 正規化、runtime header 宣言の mutable parameter 契約同期、`py_runtime_argv_storage` の TU 分離解消、`transpile_cli` 互換 shim wrapper 整理、`random/re/math` runtime 再生成である。
