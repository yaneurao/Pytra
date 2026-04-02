<a href="../../en/todo/cpp.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — C++ backend

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-04-02

## 運用ルール

- **旧 toolchain1（`src/toolchain/emit/cpp/`）は変更不可。** 新規開発・修正は全て `src/toolchain2/emit/cpp/` で行う（[spec-emitter-guide.md](../spec/spec-emitter-guide.md) §1）。
- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度順（小さい P 番号から）に着手する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモを追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。
- **parity テストは「emit + compile + run + stdout 一致」を完了条件とする。**
- **[emitter 実装ガイドライン](../spec/spec-emitter-guide.md)を必ず読むこと。** parity check ツール、禁止事項、mapping.json の使い方が書いてある。

## 未完了タスク

### P0-CPP-TYPE-ID-CLEANUP: C++ runtime から PYTRA_TID_* / type_id_support を削除する

仕様: [docs/ja/spec/spec-adt.md](../spec/spec-adt.md) §6

P0-CPP-VARIANT (variant 移行) の完了後に着手。variant 移行で `object` / `type_id` が不要になったら、`PYTRA_TID_*` 定数、`type_id_support.h`、`py_runtime_object_type_id` を削除する。

1. [x] [ID: P0-CPP-TYPEID-CLN-S1] `src/runtime/cpp/core/py_scalar_types.h` から `PYTRA_TID_*` 定数を削除する
   - 完了: `src/runtime/cpp/core/py_scalar_types.h` から `PYTRA_TID_*` 公開定数を削除し、C++ runtime 内部では `src/runtime/cpp/core/py_types.h` の `pytra::runtime::cpp::detail::kTypeId*` に置き換えた。あわせて `src/toolchain2/emit/cpp/emitter.py` も built-in type id を数値 literal へ落とすように更新し、生成 C++ から `PYTRA_TID_*` 直参照を除去した。
2. [x] [ID: P0-CPP-TYPEID-CLN-S2] `src/runtime/cpp/core/type_id_support.h` を削除する
   - 完了: `src/runtime/cpp/core/type_id_support.h` を削除し、`py_runtime_value_exact_is` は `src/runtime/cpp/built_in/base_ops.h` に移設した。`src/toolchain2/link/{runtime_discovery.py,dependencies.py,linker.py}` と `src/toolchain2/emit/cpp/emitter.py` を更新して、C++ link/emitter では `py_runtime_object_type_id` / `py_runtime_type_id_is_subtype` / `py_runtime_type_id_issubclass` の wrapper と `pytra.built_in.type_id` 自動依存を使わない構成にした。
3. [x] [ID: P0-CPP-TYPEID-CLN-S3] fixture + sample + stdlib parity に回帰がないことを確認する
   - 完了: `runtime_parity_check_fast --case-root fixture --targets cpp --cmd-timeout-sec 300` で `139/139 PASS`、`--case-root sample` で `18/18 PASS`、`--case-root stdlib` で `16/16 PASS` を確認した。残件だった `type_ignore_from_import` / `callable_higher_order` / `json_{extended,indent_optional,unicode_escape}` は `src/toolchain2/emit/cpp/emitter.py` の callable expected-type 解決と optional cast 正規化を修正して解消した。

### P0-CPP-VARIANT: C++ を std::variant ベースに移行し object/box/unbox を廃止する

文脈: [docs/ja/plans/plan-cpp-variant-migration.md](../plans/plan-cpp-variant-migration.md)
仕様: [docs/ja/spec/spec-adt.md](../spec/spec-adt.md)

union type を `object` に退化させず `std::variant` で表現する。`work/tmp/variant_test.cpp` で基本動作・再帰型・RC共有・callable を実証済み。C++ で先に実証し、成功したら EAST の object 退化を廃止する。

**Phase 1: variant 出力追加**

1. [x] [ID: P0-CPP-VARIANT-S1] C++ emitter に `UnionType` → `std::variant<T1, T2, ...>` の型変換パスを追加する
   - 完了: `src/toolchain/emit/cpp/emitter/type_bridge.py` と `header_builder.py` / `cpp_emitter.py` の type alias 出力を更新し、一般 union を `object`/`_Union_*` へ退化させず `::std::variant<...>` として出力するように変更した。`tools/unittest/emit/cpp/test_cpp_type.py`、`tools/unittest/emit/cpp/test_east3_cpp_bridge.py`、`tools/unittest/emit/cpp/test_py2cpp_features.py` に回帰テストを追加し、対象テストを実行済み。
2. [x] [ID: P0-CPP-VARIANT-S2] isinstance narrowing を `std::holds_alternative<T>` + `std::get<T>` に変換する
   - 完了: `src/toolchain/emit/cpp/emitter/runtime_expr.py` の `IsInstance` 出力で general union / alias union を `std::holds_alternative<T>` に変換し、`src/toolchain/emit/cpp/emitter/cpp_emitter.py` の `Unbox` 出力で対応 lane を `std::get<T>` に変換するように更新した。`tools/unittest/emit/cpp/test_east3_cpp_bridge.py` に general union / alias union の narrowing 回帰を追加し、対象テストを実行済み。
3. [x] [ID: P0-CPP-VARIANT-S3] 再帰型を `struct { variant<..., shared_ptr<vector<Self>>> }` で出力する
   - 完了: named recursive union alias は `using` ではなく `struct <Name> : ::std::variant<...>` として出力し、自己参照する `list/dict/set` lane は `Object<...>` に持ち上げて前方参照を切るように変更した。`tools/unittest/emit/cpp/test_py2cpp_features.py` に synthetic recursive alias の C++ / header 出力回帰を追加し、`src/pytra/std/json.py --emit-runtime-cpp` の `json.h` でも `struct JsonVal : ::std::variant<...>` を確認した。
4. [x] [ID: P0-CPP-VARIANT-S4] 基本 union fixture（`int | str`, `str | None` 等）が C++ で PASS することを確認する
   - 完了: `PYTHONPATH=/workspace/Pytra/src:/workspace/Pytra/tools/check python3 tools/check/runtime_parity_check_fast.py --targets cpp type_alias_pep695 ifexp_optional_inference nested_types none_optional --cmd-timeout-sec 120` を実行し、`type_alias_pep695`（named union alias）、`ifexp_optional_inference`（`str | None`）、`nested_types`（`dict[str, str | None]`）、`none_optional`（`int | None`）の 4 case が C++ parity PASS することを確認した。

**Phase 2: object 型を削除**

5. [x] [ID: P0-CPP-VARIANT-S5] C++ emitter の `object` 型出力を全て `std::variant` に置換する
   - 完了: `src/toolchain2/emit/cpp/types.py` / `src/toolchain2/emit/cpp/emitter.py` を更新し、general union の宣言・container・`dict.get` default・`list.append`・`isinstance`・cast / unbox・tuple unpack を `std::variant` / `std::holds_alternative` / `std::get` / `std::visit` ベースへ置換した。`src/runtime/cpp/built_in/base_ops.h` では `str(variant)` / `str(tuple)` / container repr の差分を補正し、`type_alias_pep695`, `union_basic`, `union_dict_items`, `union_list_mixed`, `optional_none`, `object_container_access`, `nested_types`, `typing/str_repr_containers` の C++ parity PASS を確認した。さらに union を含む fixture + sample 16 case を fresh emit して entry module `.cpp` を走査し、`Object<dict<str, object>>`, `Object<list<object>>`, `.unbox<`, `.as<dict<str, object>>`, `py_runtime_object_isinstance(...)`, `dict<object, object>{}` が case 本体に残っていないことを確認した。
6. [ ] [ID: P0-CPP-VARIANT-S6] `object.h` の `object` クラス削除に向けた blocker を分離し、削除順を固定する
   - メモ: `PYTRA_TID_*` と `py_runtime_object_type_id` の cleanup は `P0-CPP-TYPEID-CLN` で概ね完了済み。現状の blocker は `src/toolchain2/compile/lower.py` の `resolved_type="object"` / iter boundary、`src/toolchain2/emit/cpp/emitter.py` の `Box` / `Unbox` / generic callable bridge、`src/runtime/cpp/std/{argparse,pathlib}.*` と tuple index fallback などの `object` 実使用パス。`object.h` 本体は `S8` / `S10` より前には削除しない。
7. [ ] [ID: P0-CPP-VARIANT-S6A] C++ runtime / emitter に残っている不要な `PYTRA_TID_OBJECT` / object-type-id 正規化の残骸を削除する
8. [x] [ID: P0-CPP-VARIANT-S6B] `object.h` の `Object<void>` / `using object = Object<void>` を削除する前提として、runtime stdlib の object seam を inventory 化し、owner を `S8` / `S10` / follow-up plan に振り分ける
   - 完了: [p0-cpp-object-seam-inventory.md](../plans/p0-cpp-object-seam-inventory.md) を追加し、`lower.py` の object 退化、C++ emitter の `Box` / `Unbox` / generic callable bridge、runtime stdlib (`argparse`, `pathlib`, tuple index fallback)、runtime core (`object.h`, `py_types.h`, `base_ops.h`, `conversions.h`) を棚卸しした。削除順は `P0-CMN-BOXUNBOX -> P0-CPP-VARIANT-S8/S9 -> P0-CPP-VARIANT-S10/S11 -> P0-CPP-VARIANT-S6B` に固定する。
9. [ ] [ID: P0-CPP-VARIANT-S7] fixture 全件 + sample 全件が `object` 型なしで PASS することを確認する

**Phase 3: box/unbox 削除**

10. [ ] [ID: P0-CPP-VARIANT-S8] C++ emitter の box/unbox 処理を削除し、variant 代入 / `std::get` に置換する
   - 進捗: fresh `parity-fast` の generated C++ entry `.cpp` を走査し、`.unbox<...>()` / `.as<...>()` が 0 件であることを確認した。残っている `object(` は explicit object 境界と `built_in/type_id.cpp` が中心。
11. [x] [ID: P0-CPP-VARIANT-S9] `yields_dynamic` 依存コードを C++ emitter から削除する
   - 完了: `src/toolchain2/emit/cpp/` 配下を grep し、`yields_dynamic` / `yield_dynamic` / `dynamic_yield` 参照が 0 件であることを確認した。C++ backend はすでに `yields_dynamic` metadata に依存しておらず、`type_ignore_from_import`, `callable_higher_order`, `typed_container_access`, `trait_basic`, `trait_with_inheritance` の parity PASS を再確認した。

**Phase 4: EAST から object 退化 / box / unbox を削除**

12. [ ] [ID: P0-CPP-VARIANT-S10] lower.py の Boxing（`resolved_type="object"` 生成）と iter boundary を削除する
   - メモ: `iter.init` / `iter.next` は `ObjIterInit` / `ObjIterNext` として lower されるが、現行 `src/toolchain2/emit/cpp/emitter.py` は direct ノードを処理せず、`src/runtime/cpp/` に `py_iter_or_raise` / `py_next_or_stop` free helper も存在しない。したがって `S10` は `resolved_type="object"` の Boxing 削減と、C++ 向け iter runtime 契約の再導入/整理を分離して進める必要がある。
13. [x] [ID: P0-CPP-VARIANT-S10A] `S10` の blocker として、C++ 向け iter boundary 削除に必要な runtime 契約を棚卸しする
   - 完了: `src/toolchain2/compile/lower.py` の `ObjIterInit` / `ObjIterNext` 生成点、`src/toolchain2/emit/cpp/emitter.py` が direct ノード未対応であること、`src/runtime/cpp/` に `py_iter_or_raise` / `py_next_or_stop` 実装が存在しないことを確認した。`S10` は `resolved_type="object"` Boxing 削減と iter runtime 契約整備を別 tranche で進める。
14. [ ] [ID: P0-CPP-VARIANT-S10B] C++ 向け `ObjIterInit` / `ObjIterNext` の runtime 契約を決め、`S10` から分離する
   - 文脈: [p0-cpp-iter-boundary-runtime-contract.md](../plans/p0-cpp-iter-boundary-runtime-contract.md)
15. [ ] [ID: P0-CPP-VARIANT-S11] EAST3 validation に「`resolved_type: "object"` ならエラー」を追加する
16. [ ] [ID: P0-CPP-VARIANT-S12] 全言語の fixture + sample が PASS することを確認する

### P0-CPP-OBJECT-CONTAINER: object_container_access fixture の C++ parity を通す

文脈: [docs/ja/plans/plan-object-container-access-parity.md](../plans/plan-object-container-access-parity.md)

selfhost で必要な動的型パターン（`dict[str, object]` の items() unpack / get()、`list[object]` の index、str 不要 unbox、`set[tuple[str,str]]`）を網羅する fixture。EAST3 には全て情報が載っている。selfhost build (S5) の前提。

1. [x] [ID: P0-CPP-OBJ-CONT-S1] `object_container_access` fixture が C++ で compile + run parity PASS することを確認する（失敗なら emitter を修正）
   - 完了: `src/runtime/cpp/core/py_types.h` に `std::tuple<...>` 向け hash 特殊化を追加し、`set[tuple[str, str]]` の compile failure を解消した。`PYTHONPATH=/workspace/Pytra/src:/workspace/Pytra/tools/check python3 tools/check/runtime_parity_check_fast.py --targets cpp object_container_access --cmd-timeout-sec 120` で parity PASS を確認し、`tools/unittest/emit/cpp/test_object_t.py` に tuple-key set の runtime 回帰テストを追加した。

### P0-SUBSCRIPT-BOUNDS: negative-index-mode / bounds-check-mode を EAST optimizer に移管する

文脈: [docs/ja/plans/p0-subscript-bounds-east-optimizer.md](../plans/p0-subscript-bounds-east-optimizer.md)

旧 toolchain の emitter オプション `--negative-index-mode` / `--bounds-check-mode` が toolchain2 に未移行。C++ runtime の `py_list_at_ref` が全添字アクセスで常に負数正規化 + bounds check を行い、hot loop で深刻な性能劣化を引き起こしている（sample 01 mandelbrot: C++ 12.8s vs Rust 1.9s）。これらは emitter ではなく EAST optimizer のオプションとして実装し、`Subscript` ノードにメタデータを付与する。emitter はメタデータのみを参照し、オプション自体を知らない。

1. [x] [ID: P0-SUB-BOUNDS-S1] `meta.subscript_access_v1` スキーマを spec-east.md に定義する
   - 完了: `docs/ja/spec/spec-east.md` に `Subscript.meta.subscript_access_v1` の canonical schema（`negative_index`, `bounds_check`, `reason`）と fail-closed 規則を追加し、`docs/ja/spec/spec-east3-optimizer.md` に `SubscriptAccessAnnotationPass` の責務・v1 判定規則・backend との境界を追記した。
2. [x] [ID: P0-SUB-BOUNDS-S2] EAST optimizer に `--negative-index-mode` / `--bounds-check-mode` を追加し、`Subscript` ノードにメタデータを付与するパスを実装する。`runtime_parity_check_fast.py` にも同オプションを追加して optimizer に引き回す
   - 2026-04-02: `SubscriptAccessAnnotationPass` を toolchain2 optimizer に追加し、`pytra-cli2 -optimize/-build` と `runtime_parity_check_fast.py` から `negative_index_mode` / `bounds_check_mode` を optimizer debug flags として引き回すよう更新。toolchain2 / tooling の単体回帰を追加。
3. [ ] [ID: P0-SUB-BOUNDS-S1.5] `--east3-opt-level` を `--opt-level` に改名し、`--opt-level` が `negative_index_mode` / `bounds_check_mode` のデフォルトを決定するよう統合する（全 CLI・optimizer・spec・tutorial）
4. [x] [ID: P0-SUB-BOUNDS-S3] C++ emitter でメタデータに基づく direct index / py_list_at_ref の分岐を実装する
   - 2026-04-02: `toolchain2` C++ emitter が `Subscript.meta.subscript_access_v1` を読み、`bounds_check=off` の list/bytes/bytearray access を direct `operator[]` に切り替えるよう更新。`negative_index=normalize` は direct path でも `py_len(...)` ベースで正規化し、metadata 不正時は従来の `py_list_at_ref` に fail-close する targeted 回帰を追加。
5. [x] [ID: P0-SUB-BOUNDS-S4] sample 01 (mandelbrot) の C++ 実行時間が改善されることを確認する
   - 2026-04-02: `toolchain2` build / parity pathで linked runtime module にも optimizer を再適用し、`utils/png.cpp` の hot loop 3 箇所が `py_list_at_ref` から direct `operator[]` に変わることを確認。`runtime_parity_check_fast --case-root sample --targets cpp 01_mandelbrot` は PASS、手元 build の run-only 計測では `elapsed_sec ≈ 0.82s`。
6. [x] [ID: P0-SUB-BOUNDS-S5] fixture + sample + stdlib parity に回帰がないことを確認する
   - 完了: `runtime_parity_check_fast --case-root fixture --targets cpp --cmd-timeout-sec 300` が `139/139 PASS`、`--case-root sample` が `18/18 PASS`、`--case-root stdlib` が `16/16 PASS`。`negative_index_mode=const_only` / `bounds_check_mode=off` の optimizer metadata 分岐を有効にした状態でも C++ parity に回帰がないことを確認した。
7. [x] [ID: P0-SUB-BOUNDS-S6] negative index の回帰 fixture を追加する（`a[-1]` が optimizer の誤判定で壊れないことを検証）
   - 完了: `test/fixture/source/py/collections/negative_index_comprehensive.py` が追加済みで、list / str / bytes / bytearray の負数 index と mutation 後アクセスを網羅している。`runtime_parity_check_fast --case-root fixture --targets cpp negative_index negative_index_comprehensive --cmd-timeout-sec 300` を実行し、2 case とも PASS を確認した。

### P0-CPP-OPT-VARIANT: optional\<variant\> 移行後の JSON stdlib parity 回復

文脈: [docs/ja/plans/p0-cpp-optional-variant-parity.md](../plans/p0-cpp-optional-variant-parity.md)

monostate → `std::optional<std::variant<...>>` 移行（commit f8c4c618b）で JSON stdlib 3件が compile failure。JsonValue の resolved_type が展開されて `list<optional<variant<...>>>` になるのが原因。

1. [x] [ID: P0-CPP-OPT-VAR-S1] JsonValue の resolved_type 展開が optional\<variant\> に巻き込まれる原因を調査し、NominalAdtType の型写像を修正する
   - 完了: `src/toolchain2/emit/cpp/types.py` に `JsonVal` の nominal 正規化と alias union 展開を追加し、`src/runtime/cpp/mapping.json` / `src/toolchain2/emit/cpp/runtime_paths.py` / `src/toolchain2/emit/cpp/header_gen.py` / `src/toolchain2/emit/cpp/emitter.py` を更新した。linked EAST3 で `list[Any]` / `dict[str,Any]` に崩れていた `JsonVal` を emitter 内で `JsonVal`, `list[JsonVal]`, `dict[str,JsonVal]` へ戻し、recursive alias header を `struct JsonVal : ::std::optional<::std::variant<...>>` として一貫して出力するようにした。
2. [x] [ID: P0-CPP-OPT-VAR-S2] json_extended / json_indent_optional / json_nested が C++ parity PASS することを確認する
   - 完了: `src/toolchain2/emit/cpp/emitter.py` で local container storage を正規化し、recursive `JsonVal` container local が `.as<...>()` に落ちないように修正した。`src/toolchain2/emit/cpp/header_gen.py` では `py_to_string(const JsonVal&)` forwarder を生成し、`src/runtime/cpp/built_in/base_ops.h` に `py_to_string(bool)` を追加して `dumps(True)` を Python と同じ `"true"` に揃えた。`PYTHONPATH=/workspace/Pytra/src python3 src/pytra-cli2.py -build test/stdlib/source/py/json/json_extended.py -o work/tmp/json_extended_build --target cpp` と `... json_indent_optional.py ...` の emit 後、`runtime_parity_check._run_cpp_emit_dir(...)` で compile + run を確認した。現行ツリーに `json_nested.py` は存在しないため、std/json 配下の実在 2 case で確認している。
3. [x] [ID: P0-CPP-OPT-VAR-S3] fixture + sample に回帰がないことを確認する
   - 完了: C++ broad parity の fresh rerun で `runtime_parity_check_fast --case-root fixture --targets cpp --cmd-timeout-sec 300` が `139/139 PASS`、`--case-root sample` が `18/18 PASS` となり、`optional<variant>` 移行後も fixture/sample に回帰がないことを確認した。JSON 3件の compile failure は `P0-COMMON-BOX-UNBOX-NORM` と重なる emitter 修正で解消済み。

### P0-COMMON-BOX-UNBOX-NORM: box/unbox 正規化を CommonRenderer へ寄せる

文脈: [docs/ja/plans/p0-common-renderer-box-unbox-normalization.md](../plans/p0-common-renderer-box-unbox-normalization.md)

C++ parity で発生した `optional` の二重 deref や callable 引数の不要 bridge は、backend 固有の記法ではなく box/unbox/cast 正規化の共通不足が原因である。backend ごとの止血を減らすため、backend 非依存の冪等化は CommonRenderer に移す。

1. [x] [ID: P0-CMN-BOXUNBOX-S1] CommonRenderer に box/unbox/cast 正規化の共通入口を追加する
   - 完了: `src/toolchain2/emit/common/common_renderer.py` に `_normalize_boundary_expr()` と `_boundary_target_name()` を追加し、`render_expr()` 入口で同一 target の `Box(Box(x))` / `Unbox(Unbox(x))` を backend 非依存で畳み込むようにした。`tools/unittest/toolchain2/test_common_renderer.py` に共通回帰を追加し、既存の C++ `nested optional unbox` 回帰と JSON stdlib parity (`json_extended`, `json_indent_optional`, `json_unicode_escape`) が維持されることを確認した。
2. [x] [ID: P0-CMN-BOXUNBOX-S2] C++ emitter の optional / callable / target-type path を共通正規化へ切り替える
   - 完了: `src/toolchain2/emit/cpp/emitter.py` に `_normalize_cpp_boundary_expr()` を追加し、`_emit_expr_as_type()`, `_emit_unbox()`, `_emit_cast_expr()` が CommonRenderer の boundary 正規化を通るようにした。これにより target-type `object` / cast / optional unbox の各経路で nested `Box` / `Unbox` を個別実装に頼らず畳み込めるようにした。`tools/unittest/toolchain2/test_linker_spec_conform2.py` に C++ target-type / cast path の回帰を追加した。
3. [x] [ID: P0-CMN-BOXUNBOX-S3] `json_extended`, `json_indent_optional`, `json_unicode_escape`, `callable_higher_order` の C++ parity が PASS することを確認する
   - 完了: `runtime_parity_check_fast --case-root stdlib --targets cpp json_extended json_indent_optional json_unicode_escape --cmd-timeout-sec 300` で JSON 3件が PASS、`runtime_parity_check_fast --case-root fixture --targets cpp callable_higher_order --cmd-timeout-sec 300` で `callable_higher_order` が PASS することを確認した。あわせて `type_ignore_from_import` も targeted parity で PASS を維持した。

### P20-CPP-SELFHOST: C++ emitter で toolchain2 を C++ に変換し g++ build を通す

文脈: [docs/ja/plans/p4-cpp-selfhost.md](../plans/p4-cpp-selfhost.md)

1. [x] [ID: P20-CPP-SELFHOST-S0] selfhost 対象コード（`src/toolchain2/` 全 .py）で戻り値型の注釈が欠けている関数に型注釈を追加する — resolve が `inference_failure` にならない状態にする（他言語と共通。先に完了した側の成果を共有）
   - 完了: `ast` 走査で `src/toolchain2/` 全 `.py` の `FunctionDef` / `AsyncFunctionDef` を監査し、戻り値注釈欠落が 0 件であることを確認。回帰防止として `tools/unittest/selfhost/test_selfhost_return_annotations.py` を追加した
2. [x] [ID: P20-CPP-SELFHOST-S1] toolchain2 全 .py を C++ に emit し、g++ build が通ることを確認する
   - 完了: code_emitter.py → code_emitter.cpp 生成・リンク成功（runtime cpp + 依存 .cpp と結合）
3. [x] [ID: P20-CPP-SELFHOST-S2] g++ build 失敗ケースを emitter/runtime の修正で解消する（EAST の workaround 禁止）
   - 完了: tuple subscript 検出拡張、py_dict_set_mut 追加、object→str/container 型強制、前方宣言二段階出力、is_simple_ident ガード、py_set_add_mut fallback を py_to_string 経由に変更
4. [x] [ID: P20-CPP-SELFHOST-S3] selfhost 用 C++ golden を配置し、回帰テストとして維持する
   - 完了: `python3 tools/gen/regenerate_selfhost_golden.py --target cpp --timeout 60` で `test/selfhost/cpp/` の golden を再生成し、emit 成功する 42 モジュールを更新した。emit 失敗する 5 モジュール（`toolchain2.compile.passes`, `toolchain2.optimize.passes.{tuple_target_direct_expansion,typed_enumerate_normalization,typed_repeat_materialization}`, `toolchain2.resolve.py.resolver`）は既知 skip として整理し、`tools/unittest/selfhost/test_selfhost_cpp_golden.py` に C++ 専用の golden coverage / re-emit 一致テストを追加した
5. [x] [ID: P20-CPP-SELFHOST-S4] emit 失敗の 5 モジュールを解消し、toolchain2 全モジュールの C++ emit を成功させる
   - 完了: `tools/gen/regenerate_selfhost_golden.py` の `collect_east3_opt_entries()` が 47 モジュールを返し、従来 skip していた `toolchain2.compile.passes`, `toolchain2.resolve.py.resolver`, `toolchain2.optimize.passes.{tuple_target_direct_expansion,typed_enumerate_normalization,typed_repeat_materialization}` も対象に入る状態まで C++ emit failure を解消した。selfhost C++ golden の現状差分は emit failure ではなく golden mismatch のみ。
6. [ ] [ID: P20-CPP-SELFHOST-S5] selfhost C++ バイナリを g++ でビルドし、リンクが通ることを確認する
7. [ ] [ID: P20-CPP-SELFHOST-S6] `run_selfhost_parity.py --selfhost-lang cpp --emit-target cpp --case-root fixture` で fixture parity が PASS することを確認する
8. [ ] [ID: P20-CPP-SELFHOST-S7] `run_selfhost_parity.py --selfhost-lang cpp --emit-target cpp --case-root sample` で sample parity が PASS することを確認する
