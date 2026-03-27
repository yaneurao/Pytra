<a href="../../../en/plans/archive/20260317-p2-cpp-pyruntime-upstream-fallback-shrink.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P2: C++ `py_runtime.h` の upstream fallback shrink

最終更新: 2026-03-17

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01`

背景:
- `docs/ja/plans/archive/20260312-p5-cpp-pyruntime-residual-thin-seam-shrink.md` では、`py_runtime.h` の residual seam を `py_append(object& ...)` と shared `type_id` thin seam に分類し、縮退順だけを固定した。
- しかし `src/runtime/cpp/native/core/py_runtime.h` 自体は 2026-03-14 時点で 1287 行あり、まだ object bridge 互換、generic `make_object` / `py_to`、typed collection fallback が大きな塊として残っている。
- 現行 caller を見ると、`sample/cpp` の `py_append(` bucket と generic index bucket は retire 済みで、`src/runtime/cpp/generated/**` 側の object-list bridge と generic index bucket も除去できた。typed-lane residual は emitter helper-only まで縮退している。
- `src/runtime/cpp/generated/core/README.md` が明示する通り、`generated/core` は `py_runtime.h` の肥大化逃がし用 bucket ではない。したがって、単なる物理分割ではなく、typed lane で upstream に押し戻せる fallback を減らす必要がある。

目的:
- `py_runtime.h` を物理分割ではなく upstream 側の責務整理で縮める。

> **長期方針との関係:** `P5-ANY-ELIM-OBJECT-FREE-01` が `Any` 禁止 → `object`/`PyObj` 完全除去を長期目標として定義している。本タスクはその前準備として typed-lane の fallback caller を削減する作業であり、P5 達成時に本タスクの成果が超越される。
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
- [x] [ID: P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01-S2-01] typed list mutation / indexing / tuple-list boxing の emit を改善し、`py_append(object&)` と `py_at(object, idx)` の caller を削減する。
- [x] [ID: P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01-S2-02] generated built_in/std runtime と representative sample の object-bridge fallback を減らし、baseline を更新する。
- [x] [ID: P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01-S2-03] generic `make_object` / `py_to` / dict-key coercion の typed path fallback を縮退し、`Any/object` 境界へ寄せる。
- [x] [ID: P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01-S3-01] regression / checker / docs / English mirror を同期し、`py_runtime.h` shrink の current contract を閉じる。

決定ログ:
- 2026-03-14: `py_runtime.h` はまだ縮むが、次段は header 分割ではなく typed fallback を EAST3 / emitter / runtime SoT に押し戻す task と判断し、P2 として起票した。
- 2026-03-14: residual thin-seam checker 群は archive 済み `P5` を active follow-up として参照していたため、この `P2` を current owner として rebasing し、bundle order も active な `S1-01..S3-01` shrink contract に揃える。
- 2026-03-14: `S1-01` として `src/toolchain/compiler/cpp_pyruntime_upstream_fallback_inventory.py` / `tools/check_cpp_pyruntime_upstream_fallback_inventory.py` を追加し、header bulk anchor 9 件、C++ emitter residual 2 種、generated runtime residual 3 種、sample residual 2 種を machine-readable inventory と unit test で固定した。
- 2026-03-14: 2026-03-14 時点の baseline は `src/runtime/cpp/native/core/py_runtime.h` 1287 行、header `py_to<*>(...object...)` 5 件、`src/backends/cpp/emitter/**` の `obj_to_list_ref_or_raise(` 2 件 / `make_object(list<object>{})` 3 件、`src/runtime/cpp/generated/**` の `obj_to_list_ref_or_raise(` 2 件 / `make_object(list<object>{})` 3 件 / `py_at(...py_to<int64>)` 46 件、`sample/cpp/**` の `py_append(` 41 件 / `py_at(...py_to<int64>)` 39 件とする。
- 2026-03-14: `S1-02` として `src/toolchain/compiler/cpp_pyruntime_upstream_fallback_contract.py` / `tools/check_cpp_pyruntime_upstream_fallback_contract.py` を追加し、header bulk を `object_only_compat_header` 4 件、`any_object_boundary_header` 5 件、`typed_lane_must_not_use` 7 件へ partition した。
- 2026-03-14: final handoff guard には upstream fallback boundary checker/test を追加し、active `P2` handoff が inventory baseline と boundary contract の両方を参照するようにした。
- 2026-03-14: `S2-01` の first bundle として、empty pyobj runtime list literal の seed を generic `make_object(list<object>{})` から direct `object_new<PyListObj>(list<object>{})` へ切り替え、C++ emitter residual から `cpp_emitter_boxed_list_seed_sites` bucket を除去した。残る emitter-side typed-lane residual は `obj_to_list_ref_or_raise(` helper 1 bucket のみ。
- 2026-03-14: `S2-01` の second bundle として、pyobj runtime list `extend` の inline `obj_to_list_ref_or_raise({boxed_value}, ...)` site を共通 helper 経由へ畳み、`cpp_emitter_object_list_bridge_sites` を helper 定義 1 箇所だけに縮めた。これで emitter-side residual は source literal としても helper-only になった。
- 2026-03-14: `S2-01` は emitter 側 residual を helper-only まで縮退できたため完了扱いにした。
- 2026-03-14: `S2-02` の first bundle として `src/py2x.py --target cpp src/pytra/built_in/iter_ops.py --emit-runtime-cpp` と `src/py2x.py --target cpp src/pytra/utils/gif.py --emit-runtime-cpp` の正規導線で `generated/built_in/iter_ops.cpp` と `generated/utils/gif.{h,cpp}` を再生成した。これで `generated_runtime_boxed_list_seed_sites` は `3 -> 1` まで縮退し、残りは `generated/utils/gif.cpp` の `bytes(make_object(list<object>{}))` のみになった。
- 2026-03-14: `S2-02` の second bundle として `src/pytra/utils/gif.py` の empty `bytes` seed を typed `list[int]` へ upstream し、`generated/utils/gif.cpp` の最後の `bytes(make_object(list<object>{}))` site を retire した。これで typed-lane residual は emitter 1 / generated 2 / sample 2 bucket になり、`generated_runtime_boxed_list_seed_sites` は inventory / contract から除去した。
- 2026-03-14: `S2-02` の third bundle として representative sample の `07_game_of_life_loop` と `12_sort_visualizer` を direct typed append / size lane へ再生成し、`sample_cpp_py_append_sites` baseline を `41 -> 34` に更新した。`18_mini_language_interpreter` は別の sample/emitter regression を露呈したためこの bundle からは除外し、sample 側の残 bucket は可視化 sample 群と `18_mini_language_interpreter` の parser/benchmark helper に集中している。
- 2026-03-14: `S2-02` の fourth bundle として `18_mini_language_interpreter` の token/parser/benchmark helper を direct typed append / size lane に寄せ、`sample_cpp_py_append_sites` baseline を `34 -> 7` に更新した。sample 側の残 bucket は `13_maze_generation_steps` の tuple/frame helper lane に集中している。
- 2026-03-14: `S2-02` の fifth bundle として `sample/cpp` の最後の `py_append(` residual を retire し、`sample_cpp_py_append_sites` を inventory から除去した。sample 側の typed residual は `py_at(...py_to<int64>)` の generic index bucket だけになった。
- 2026-03-14: `S2-02` の sixth bundle として `src/pytra/built_in/predicates.py` を object index loop から iterator lane へ寄せ、`generated_runtime_generic_index_sites` baseline を `46 -> 44` に縮退させた。残件は `iter_ops`, `type_id`, `std/*`, `utils/png` に集中している。
- 2026-03-14: `S2-02` の seventh bundle として `list[object]` を C++ `pyobj` lane でも value-model list として扱えるようにし、`src/pytra/built_in/iter_ops.py` の戻り型を `list[object]` へ引き上げて `generated_runtime_object_list_bridge_sites` を retire した。typed-lane residual の bucket 数は emitter 1 / generated 1 / sample 1 になった。
- 2026-03-14: `S2-02` の eighth bundle として `src/pytra/built_in/iter_ops.py` の object helper 本文自体を iterator lane に寄せ、`generated_runtime_generic_index_sites` baseline を `44 -> 42` に縮退させた。残件は `type_id`, `std/*`, `utils/png` に集中している。
- 2026-03-14: `S2-02` の ninth bundle として `tools/check_crossruntime_pyruntime_residual_caller_inventory.py` と対応 unit test を current generated `py_runtime_value_*` thin seam へ同期し、`json.cpp` / `type_id.cpp` の generated C++ residual を `generated_cpp_shared_type_id_residual` 1 bucket に再分類した。stale `generated_cpp_object_bridge_residual` bucket は retire し、crossruntime residual caller checker を現行 generated caller 実態に揃えた。
- 2026-03-14: `S2-02` の tenth bundle として C++ emitter の ref-first typed list subscript を `py_at(...py_to<int64>)` から `py_list_at_ref(rc_list_ref(...), ...)` へ切り替え、`type_id/json/argparse/random/re/png` の generated runtime と representative sample 6 本を正規導線で再生成した。これで `generated_runtime_generic_index_sites` と `sample_cpp_generic_index_sites` はともに 0 まで縮退して retire し、typed-lane residual は emitter helper 1 bucket のみになった。`S2-02` は完了。
- 2026-03-14: `S2-03` の first bundle として `py_runtime.h` に `py_coerce_cstr_typed_value()` を追加し、`list` append/set と `dict` key の `const char*` lane を `py_to<T>(make_object(str(...)))` から narrow helper へ寄せた。これで `header_dict_key_charptr_object_coercion` bucket は retire し、header の `py_to<...>(...object...)` residual は unsupported-target guard 1 件だけになった。
- 2026-03-17: `S2-03` の second bundle として emitter 側 const メソッド修飾（non-mutating method に `const` qualifier）、nested list rvalue の不要な `rc_list_ref` 除去（`py_list_at_ref` の中間結果に不要な rc_list_ref を除去）、collection literal boxing を `make_object(list<object>{})` から `object_new<PyListObj>()` に統一し、test を同期した。また generic `make_object<T>` テンプレートの `str -> bool` 誤変換バグ（`str::operator bool()` で `is_convertible_v<str, bool>` が真になり dict key が PyBoolObj になる問題）を `!is_convertible_v<T, str>` guard で修正した。これで `test_cpp_runtime_iterable.py` の `test_runtime_iterable_protocol_helpers` も通るようになった。S2-03 完了。
- 2026-03-17: `S3-01` として regression / checker / docs / English mirror を同期。S2-03 完了後の状態で `check_cpp_pyruntime_upstream_fallback_inventory.py`・`check_cpp_pyruntime_header_surface.py` ともに [OK]、全 unit test（test_cpp_runtime_iterable / test_east3_cpp_bridge / test_py2cpp_codegen_issues / tooling inventory）通過。P1-CPP-SUBSCRIPT-IDX-OPT-01 の identity cast 省略最適化（emitter subscript index guard）は別タスクとして完了済み。P2 タスク全体を閉じ、plan / archive / todo を最終形に同期。
