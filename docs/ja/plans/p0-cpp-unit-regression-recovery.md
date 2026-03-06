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

- [ ] [ID: P0-CPP-REGRESSION-RECOVERY-01] C++ unit 回帰を、SoT/IR/Emitter/Runtime 契約の順で根本修復し、unit + fixture/sample parity を再緑化する。
- [ ] [ID: P0-CPP-REGRESSION-RECOVERY-01-S1-01] failing test を「generated runtime」「import/include 解決」「container 意味論」「emitter/CLI 契約」に再分類し、修正責務の所属レイヤを固定する。
- [ ] [ID: P0-CPP-REGRESSION-RECOVERY-01-S2-01] `json` generated runtime の破綻を、SoT と C++ runtime 生成契約の修正で解消する（`.gen.*` 手修正禁止）。
- [ ] [ID: P0-CPP-REGRESSION-RECOVERY-01-S2-02] `argparse` generated runtime の破綻を、SoT・reserved name 回避・class/member emission 契約の修正で解消する。
- [ ] [ID: P0-CPP-REGRESSION-RECOVERY-01-S3-01] `pytra.utils.{png,gif}` と `pytra.std.{time,pathlib}` の import 解決・include dedupe/sort・one-to-one module include 契約を修正する。
- [ ] [ID: P0-CPP-REGRESSION-RECOVERY-01-S3-02] `os.path` / `glob` 系 runtime helper 呼び出しを、owner/module metadata に基づく解決へ戻し、C++ emitter の特例依存を減らす。
- [ ] [ID: P0-CPP-REGRESSION-RECOVERY-01-S4-01] `dict.items()` / `dict.get()` / `any()` / dict/set comprehension の container-view・iterator 意味論を、built_in SoT と runtime adapter の整合で修正する。
- [ ] [ID: P0-CPP-REGRESSION-RECOVERY-01-S4-02] `mod_mode`、stmt dispatch fallback、CLI `dump-options` / error category の C++ emitter 契約を整理し、option 反映と診断整合を修正する。
- [ ] [ID: P0-CPP-REGRESSION-RECOVERY-01-S5-01] C++ unit 全体、fixture parity、sample parity を再実行し、回帰が残らないことを確認して docs/ja/todo を更新する。

決定ログ:
- 2026-03-06: `tools/runtime_parity_check.py --targets cpp --case-root fixture` と `--case-root sample --all-samples` は通過した一方、`python3 -m unittest discover -s test/unit/backends/cpp -p test_*.py` は未通過であることを確認した。以後の修正対象は unit suite の実障害に絞る。
- 2026-03-06: `build_multi_cpp.py` と fixture compile helper を「実際に include された runtime source だけを compile」する方式へ修正済みのため、`json.gen.*` / `argparse.gen.*` compile break は build 導線の偽陽性ではなく生成契約の破綻として扱う。
- 2026-03-06: 本計画では、`.gen.*` の直接修正を禁止し、SoT・IR/lower・emitter・runtime 生成契約のどこで壊れたかを固定してから修正する。
