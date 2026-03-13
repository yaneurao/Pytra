# P2: C++ `py_runtime.h` の upstream fallback shrink

最終更新: 2026-03-14

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01`

背景:
- `docs/ja/plans/archive/20260312-p5-cpp-pyruntime-residual-thin-seam-shrink.md` では、`py_runtime.h` の residual seam を `py_append(object& ...)` と shared `type_id` thin seam に分類し、縮退順だけを固定した。
- しかし `src/runtime/cpp/native/core/py_runtime.h` 自体は 2026-03-14 時点で 1287 行あり、まだ object bridge 互換、generic `make_object` / `py_to`、typed collection fallback が大きな塊として残っている。
- 現行 caller を見ると、`sample/cpp` には `py_append(` が 41 箇所残り、`src/runtime/cpp/generated/**` にも `py_at(values, py_to<int64>(i))`、`obj_to_list_ref_or_raise(out, "append")`、`make_object(list<object>{})` のような object-bridge 依存が残っている。
- `src/runtime/cpp/generated/core/README.md` が明示する通り、`generated/core` は `py_runtime.h` の肥大化逃がし用 bucket ではない。したがって、単なる物理分割ではなく、typed lane で upstream に押し戻せる fallback を減らす必要がある。

目的:
- `py_runtime.h` を物理分割ではなく upstream 側の責務整理で縮める。
- typed list/dict/indexing/mutation と boxing/unboxing の判断を EAST3 / C++ emitter / runtime SoT 側へ押し戻し、`object` fallback を減らす。
- `Any/object` 境界だけに必要な汎用 helper を残し、typed lane では direct typed expression か narrower helper を使う構造へ寄せる。

対象:
- `src/runtime/cpp/native/core/py_runtime.h`
- `src/backends/cpp/emitter/**` の list/index/mutation/boxing/type bridge
- 必要なら EAST3 optimization / lowering で処理できる typed fallback 縮退
- `src/runtime/cpp/generated/built_in/**`, `src/runtime/cpp/generated/std/**`, `sample/cpp/**` の residual caller
- `py_runtime.h` shrink baseline を固定する docs / tooling / regression

非対象:
- `py_runtime.h` の単純な物理分割や include 逃がし
- `shared type_id` thin seam の cross-runtime redesign
- `PyObj` object model 自体の全面 redesign
- `py_div` / `py_floordiv` / `py_mod` の意味論変更

受け入れ基準:
- typed lane が `py_append(object&)`, `py_at(object, idx)`, `obj_to_list_ref_or_raise(...)` を常用せず、explicit な object-only compat caller に閉じる。
- `sample/cpp/**` と `src/runtime/cpp/generated/**` の current residual caller が baseline から減少し、shrink 後の inventory が docs/tooling に固定される。
- generic `make_object(const T&)` / `py_to<T>(object)` fallback は `Any/object` 境界へ寄り、typed 既知 path では direct typed expression または narrower helper を使う。
- `generated/core` を肥大化逃がし bucket とせずに `py_runtime.h` の行数または source-wide caller inventory が実際に減る。
- representative regression / checker / English mirror が current shrink contract に同期する。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `rg -n "\\bpy_append\\(|\\bpy_at\\([^\\n]*object|obj_to_list_ref_or_raise\\(|make_object\\(list<object>\\{|py_to<[^>]+>\\(.*object" src/runtime/cpp src/backends/cpp sample/cpp test/unit/backends/cpp -S`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_cpp_runtime_iterable.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_east3_cpp_bridge.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_codegen_issues.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_cpp_pyruntime_upstream_fallback_inventory.py'`
- `python3 tools/check_cpp_pyruntime_upstream_fallback_inventory.py`
- `python3 tools/check_cpp_pyruntime_header_surface.py`
- `git diff --check`

## 方針

- `py_runtime.h` を減らす主戦場は runtime header ではなく caller 側に置く。
- `py_append(object&)` は object-only compat seam とみなし、typed list append は emitter が `py_list_append_mut` や direct append を選ぶ。
- `py_at(object, idx)` は typed index plan が立つ場所では使わず、typed subscript / tuple destructure / list iteration へ押し戻す。
- dict key coercion や tuple/list boxing の generic fallback は、型が既知なら emitter か EAST3 で narrower expression に畳む。
- shared `type_id` thin seam はこの task の主対象にせず、caller 増殖を止める範囲に留める。

## 分解

- [x] [ID: P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01-S1-01] `py_runtime.h` の current bulk と `sample/cpp` / `generated/**` / C++ emitter の residual caller を inventory 化し、upstream へ押し戻せる fallback を分類する。
- [x] [ID: P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01-S1-02] `object-only compat` と `typed lane must not use` の境界を shrink contract として docs / tooling へ固定する。
- [ ] [ID: P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01-S2-01] typed list mutation / indexing / tuple-list boxing の emit を改善し、`py_append(object&)` と `py_at(object, idx)` の caller を削減する。
- [ ] [ID: P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01-S2-02] generated built_in/std runtime と representative sample の object-bridge fallback を減らし、baseline を更新する。
- [ ] [ID: P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01-S2-03] generic `make_object` / `py_to` / dict-key coercion の typed path fallback を縮退し、`Any/object` 境界へ寄せる。
- [ ] [ID: P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01-S3-01] regression / checker / docs / English mirror を同期し、`py_runtime.h` shrink の current contract を閉じる。

決定ログ:
- 2026-03-14: `py_runtime.h` はまだ縮むが、次段は header 分割ではなく typed fallback を EAST3 / emitter / runtime SoT に押し戻す task と判断し、P2 として起票した。
- 2026-03-14: residual thin-seam checker 群は archive 済み `P5` を active follow-up として参照していたため、この `P2` を current owner として rebasing し、bundle order も active な `S1-01..S3-01` shrink contract に揃える。
- 2026-03-14: `S1-01` として `src/toolchain/compiler/cpp_pyruntime_upstream_fallback_inventory.py` / `tools/check_cpp_pyruntime_upstream_fallback_inventory.py` を追加し、header bulk anchor 9 件、C++ emitter residual 2 種、generated runtime residual 3 種、sample residual 2 種を machine-readable inventory と unit test で固定した。
- 2026-03-14: 2026-03-14 時点の baseline は `src/runtime/cpp/native/core/py_runtime.h` 1287 行、header `py_to<*>(...object...)` 5 件、`src/backends/cpp/emitter/**` の `obj_to_list_ref_or_raise(` 2 件 / `make_object(list<object>{})` 3 件、`src/runtime/cpp/generated/**` の `obj_to_list_ref_or_raise(` 2 件 / `make_object(list<object>{})` 3 件 / `py_at(...py_to<int64>)` 47 件、`sample/cpp/**` の `py_append(` 41 件 / `py_at(...py_to<int64>)` 39 件とする。
- 2026-03-14: `S1-02` として `src/toolchain/compiler/cpp_pyruntime_upstream_fallback_contract.py` / `tools/check_cpp_pyruntime_upstream_fallback_contract.py` を追加し、header bulk を `object_only_compat_header` 4 件、`any_object_boundary_header` 5 件、`typed_lane_must_not_use` 7 件へ partition した。
- 2026-03-14: final handoff guard には upstream fallback boundary checker/test を追加し、active `P2` handoff が inventory baseline と boundary contract の両方を参照するようにした。
