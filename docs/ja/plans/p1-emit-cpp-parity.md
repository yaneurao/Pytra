<a href="../../en/plans/p1-emit-cpp-parity.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P1: toolchain2 C++ emitter の runtime 整合と parity 完了

最終更新: 2026-03-27

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-EMIT-CPP-S2`
- `docs/ja/todo/index.md` の `ID: P1-EMIT-CPP-S3`
- `docs/ja/todo/index.md` の `ID: P1-EMIT-CPP-S9`
- `docs/ja/todo/index.md` の `ID: P1-EMIT-CPP-S10`

## 背景

`toolchain2/emit/cpp/` の C++ emitter 自体は導入済みだが、runtime 側と build 経路には旧 `toolchain/` 時代の前提が残っている。特に runtime header/source 生成、native companion の取り込み、CLI build 配線、sample parity の確認が 1 つの TODO に混在しており、進捗と完了条件が見えにくい。

また [spec-emitter-guide.md](../spec/spec-emitter-guide.md) に照らすと、C++ emitter / runtime 周辺には以下の整理が必要である。

- emitter は EAST3 だけをレンダリングし、旧 `toolchain` 由来の型系や header builder に依存しない
- runtime symbol 解決は `mapping.json` / metadata / loader に寄せ、モジュール ID ハードコードを増やさない
- `src/runtime/cpp/` は既存分割構成を維持しつつ、新パイプラインの出力と整合させる

## 目的

`P1-EMIT-CPP-S2` と `P1-EMIT-CPP-S3` を、guide 準拠の runtime 整合と parity 完了まで持っていく。

## 対象

- `src/toolchain2/emit/cpp/`
- `src/runtime/cpp/`
- `src/pytra-cli.py`
- `src/pytra-cli2.py`
- C++ parity に必要な test / tooling

## 非対象

- `toolchain2/emit/go/` など他 backend の追加改善
- selfhost 完成 (`P2-SELFHOST-S4`)
- `int32` 既定化 (`P4-INT32`)

## 受け入れ基準

- `src/runtime/cpp/` が toolchain2 C++ emitter 出力と整合し、旧 `toolchain` 由来の header/type 前提を持ち込まない
- `pytra-cli.py` / `pytra-cli2.py` の C++ build 経路が toolchain2 ベースで成立する
- sample 18 件が `emit + g++ compile + run + stdout 一致` を満たす

## 確認コマンド

- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest test.unit.toolchain2.test_linker_spec_conform2 -v`
- `python3 tools/runtime_parity_check.py --targets cpp --cmd-timeout-sec 60 --case-root sample --all-samples`

## 子タスク

- [x] [ID: P1-EMIT-CPP-S2-01] runtime symbol 解決と include/path 解決を `mapping.json` / metadata ベースに寄せ、module ID ハードコードと旧 include fallback を整理する。
- [x] [ID: P1-EMIT-CPP-S2-02] runtime bundle の header/source 生成を toolchain2 C++ 型系に揃え、旧 `toolchain.emit.cpp.emitter.header_builder` 依存を除去する。
- [x] [ID: P1-EMIT-CPP-S2-03] `pytra-cli.py` / `pytra-cli2.py` の C++ build 経路で runtime bundle と native companion を正しく取り込み、representative fixture compile を通す。
- [x] [ID: P1-EMIT-CPP-S3-01] sample 18 件の C++ `emit + g++ compile` を通す。
- [x] [ID: P1-EMIT-CPP-S3-02] sample 18 件の `run + stdout 一致` を確認し、`runtime_parity_check.py --targets cpp` を通す。

## 決定ログ

- 2026-03-27: 初版作成。`P1-EMIT-CPP-S2` と `P1-EMIT-CPP-S3` は粒度が大きく、runtime 整合、build 配線、parity 実行が混在していたため、実作業単位の子タスクへ分解した。
- 2026-03-27: 現時点の主要ブロッカーは `runtime_bundle.py` が runtime `.cpp` を toolchain2 方式で生成する一方、header 側に旧 `toolchain` の型系が混入し、`py_assert_all(std::vector<bool>, std::string)` と旧 `Object<list<bool>>` 宣言が食い違う点である。まず `S2-02` を優先する。
- 2026-03-27: `S2-01` から `S2-03` を完了。`runtime_paths.py` / `dependencies.py` / `mapping.json` で runtime symbol と include 解決を metadata ベースへ寄せ、`header_gen.py` / `runtime_bundle.py` / `emitter.py` で toolchain2 C++ 型系へ統一した。`pytra-cli.py test/fixture/source/py/stdlib/path_stringify.py --target cpp` が compile 成功し、`test_linker_spec_conform2` の runtime bundle/pathlib 回帰も通過。
- 2026-03-27: `S3-01` / `S3-02` を完了。native companion-only runtime module の extern 宣言を header に残すよう `runtime_bundle.py` / `header_gen.py` を修正し、`io.h` の core 型循環を復旧、`ObjStr` を `py_to_string` lane へ統一した。加えて C++ emitter で `image.save_gif.keyword_defaults` adapter を描画し、`pytra.std.template` を type-only dependency として include から除外した。`python3 tools/runtime_parity_check.py --case-root sample --all-samples --targets cpp --cmd-timeout-sec 60` は `18/18` pass。
- 2026-03-27: runtime EAST の正本生成を legacy `toolchain` から toolchain2 (`parse -> resolve -> lower`) へ切り替え、`open -> PyFile` の resolver typing、type-predicate 用 `pytra.built_in.type_id` 依存注入、nominal class の `type_id`/`Box`/`cast`/`isinstance` 描画、`dict` 直反復の key lane を C++ emitter に追加した。`json_extended`、`17_monte_carlo_pi`、`18_mini_language_interpreter`、および sample compile sweep `18/18` を確認。
- 2026-03-27: `S8` を完了。C++ の container 既定表現を `Object<list<T>>` / `Object<dict<K,V>>` / `Object<set<T>>` に揃え、`container_value_locals_v1` が付いた局所だけ値型へ縮退させるよう `types.py` / `emitter.py` / `src/runtime/cpp/` を更新した。`dict_wrapper_methods.py` と `set_wrapper_methods.py` の C++ build+run を確認し、`json_extended` に残る failure は runtime bundle 別件として切り分けた。
- 2026-03-27: `S9` を完了。runtime module の rel-tail 解決を `link/runtime_discovery.py` の shared helper に移し、`emit/cpp/runtime_paths.py` の `pytra.built_in/std/utils/core` prefix/path 規約ハードコードを削除した。C++ emitter 側の `pytra.core.py_runtime` 個別分岐も include path の共通解決に置き換え、focused runtime path / include regression を追加した。
- 2026-03-27: `S10` を完了。`runtime/cpp/mapping.json` に `py_int_from_str` / `py_float_from_str` の native 写像を移し、C++ emitter から `append → push_back`、container helper、string-to-number cast の個別分岐を削除した。attribute call でも runtime metadata があれば mapping 解決を優先し、focused regression と representative C++ build で確認した。
- 2026-03-27: `S11` を完了。C++ emitter の `main_guard_body` / `main()` 出力は `emit_context.is_entry` を唯一の正本に揃え、library module (`is_entry=False`) では main guard と entrypoint を生成しないよう修正した。entry module は従来どおり `__pytra_main_guard()` を保持し、focused regression を追加した。
- 2026-03-27: `S12` を完了。C++ emitter に残っていた `/* slice */` と `/* assign */` placeholder を廃止し、`unsupported_slice_shape` / `unsupported_assign_target` で fail-fast するよう修正した。既存の fail-closed 群と合わせて focused regression を追加した。
- 2026-03-27: `S13` を完了。共通 `RuntimeMapping` に `implicit_promotions` を追加し、C++ `mapping.json` に整数/float の暗黙昇格表を定義した。`BinOp.casts` はこの表に一致する場合のみ省略し、非該当 cast は `static_cast` を維持するよう修正し、focused regression で確認した。
- 2026-03-27: `S14` を完了。C++ backend helper に残っていた type-only module と `pytra.core.*` helper skip の具体名を shared helper へ移した。`runtime_paths.py` は `link/dependencies.py:is_type_only_dependency_module_id()` と `runtime_discovery.py:is_runtime_internal_helper_module()` を使う薄い adapter へ縮退し、focused runtime path regression を通した。
- 2026-03-27: `S15` を完了。`_emit_attribute()` が `attribute_access_kind == "property_getter"` を見たとき、C++ では member access ではなく `obj.method()` を emit するよう修正した。`test_cpp_emitter_calls_property_getters_with_parens` と `runtime_parity_check.py --targets cpp property_method_call` で回帰確認した。
