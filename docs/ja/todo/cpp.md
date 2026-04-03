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

### P0-OBJECT-ZERO: resolved_type:"object" 残存ノードをゼロにする

`resolved_type: "object"` を EAST3 validator で全面禁止するための前提。現在 3 fixture に 6 ノード残存:

- `trait_basic` / `trait_with_inheritance`: trait デコレータの `__call__` が `cls: object` を返す → `@template` の型パラメータ `T` にすべき（EAST compile/resolve の変更）
- `typed_container_access`: `dict.get()` の結果が `object` に退化 → EAST3 の型推論バグ（compile/resolve の変更）

trait の `cls` を型パラメータにするのと `dict.get` の型推論修正は EAST compile/resolve の変更。修正後に S11（validator で全面禁止）に着手。

1. [x] [ID: P0-OBJ-ZERO-S1] trait デコレータの `cls` を `@template` 型パラメータ `T` に変更する（EAST compile/resolve）
   - 完了メモ: resolver で trait helper の `__call__` 形を正規化し、identity decorator の `cls: object -> object` を `T -> T`、implements factory の `-> object` を具体 helper 型へ置き換えた。`trait_basic`, `trait_with_inheritance` の C++ parity `PASS` と、対象 fixture の `resolved_type="object"` 0 件を確認した。
2. [x] [ID: P0-OBJ-ZERO-S2] `typed_container_access` の `dict.get()` が value 型を返すように型推論を修正する（EAST compile/resolve）
   - 完了メモ: `dict.get(key, default)` が `dict[..., object]` でも concrete default を持つ場合はその default 型へ寄せるよう resolver を修正した。`typed_container_access` の C++ parity `PASS` と、`od.get("name", "")` の `resolved_type == "str"` / `call_arg_type == "str"` を unit test で固定した。
3. [x] [ID: P0-OBJ-ZERO-S3] 影響する fixture の EAST3 golden を再生成し、`resolved_type: "object"` がゼロであることを確認する（対象 fixture のみ再生成）
   - 完了メモ: `trait_basic`, `trait_with_inheritance`, `typed_container_access` の `east1/east2/east3/east3-opt/linked` を再生成した。あわせて `fixture + sample + stdlib + src/pytra` を C++ 向け lower で再走査し、`resolved_type="object"` の残件が 0 であることを確認した。runtime east も `tools/check/check_east3_golden.py --check-runtime-east --update` で再生成し、freshness `31 ok, 0 stale` を確認した。
4. [x] [ID: P0-OBJ-ZERO-S4] P0-CPP-VARIANT-S11 を実行する（EAST3 validator に「`resolved_type: "object"` ならエラー」を追加）
   - 完了メモ: `toolchain2.compile.validate_east3` を追加し、`lower_east2_to_east3()` の完了時に validator を実行して `resolved_type: "object"` を fail-fast にした。`test_validate_east3_rejects_object_resolved_type` と `test_compile_rejects_object_resolved_type_in_east3` を追加し、object zero 化した `trait_basic` / `typed_container_access` 回帰とあわせて unit test を通した。

### P0-CPP-LINT-PYRANGE: emitter の "py_range" ハードコードを削除する

`emitter.py:1699` で `runtime_call == "py_range"` を文字列で判定している（lint `runtime_symbol` 違反）。`in x in range(n)` の最適化で range 呼び出しかどうかを判定する処理。

spec-east.md §4 で `range()` は EAST 構築段階で `RangeExpr` に lower されるため、`runtime_call` で判定する必要はない。`RangeExpr` ノードの kind を見るか、`semantic_tag` で判定すべき。

1. [x] [ID: P0-CPP-LINT-PYRANGE-S1] `_emit_range_call_contains_expr` を `RangeExpr` ノード判定に変更し、`"py_range"` ハードコードを削除する
   - 完了メモ: `_emit_range_call_contains_expr()` は `RangeExpr` の `start/stop/step` を直接見るように変更し、`runtime_call == "py_range"` の文字列判定を撤去した。従来の `Call(args=...)` fallback は維持している。
2. [x] [ID: P0-CPP-LINT-PYRANGE-S2] `check_emitter_hardcode_lint.py --lang cpp` で `runtime_symbol` が 0 件になることを確認する
   - 完了メモ: `check_emitter_hardcode_lint.py --lang cpp` は 0 件、`runtime_parity_check_fast --case-root fixture --targets cpp in_membership --opt-level 1` も `PASS` を確認した。

### P0-CPP-VARIANT: C++ を std::variant ベースに移行し object/box/unbox を廃止する

文脈: [docs/ja/plans/plan-cpp-variant-migration.md](../plans/plan-cpp-variant-migration.md)
仕様: [docs/ja/spec/spec-adt.md](../spec/spec-adt.md)

Phase 1（variant 出力追加）、Phase 2 の S5 まで完了済み（[archive/20260402.md](archive/20260402.md) 参照）。

**Phase 2: object 型を削除（残）**

1. [x] [ID: P0-CPP-VARIANT-S6] `object.h` の `object` クラス削除に向けた blocker を分離し、削除順を固定する
   - 完了メモ: blocker は `P0-CPP-VARIANT-S6A`, `P0-CPP-VARIANT-S10A`, `P0-CPP-VARIANT-S10B` に分割して固定した。`object.h` 削除前の seam は [p0-cpp-object-seam-inventory.md](../plans/p0-cpp-object-seam-inventory.md) に棚卸しし、iter boundary の残件は [p0-cpp-iter-boundary-runtime-contract.md](../plans/p0-cpp-iter-boundary-runtime-contract.md) に切り出した。現時点で non-explicit dynamic path の `resolved_type=\"object\"` は除去済みで、残件は explicit object / bare `Callable` / iter runtime 契約に限定されている。
2. [x] [ID: P0-CPP-VARIANT-S6A] C++ runtime / emitter に残っている不要な `PYTRA_TID_OBJECT` / object-type-id 正規化の残骸を削除する
   - 完了メモ: `isinstance(x, object)` / `issubclass(X, object)` は lower で constant `True` に潰すようにし、`_builtin_type_id_symbol()` から `object -> PYTRA_TID_OBJECT` を削除した。あわせて C++ emitter の `PYTRA_TID_OBJECT -> object` 正規化も撤去し、`src/toolchain2/emit/cpp`, `src/toolchain2/compile`, `src/runtime/cpp` 直下の `PYTRA_TID_OBJECT` 残件は 0 を確認した。
3. [x] [ID: P0-CPP-VARIANT-S7] fixture 全件 + sample 全件が `object` 型なしで PASS することを確認する
   - 完了メモ: fresh in-memory probe で `in_membership`, `iterable`, `callable_higher_order`, `finally`, `float`, `type_ignore_from_import` を再確認し、generated C++ entry `.cpp` から `object(` / `.unbox<...>()` / `.as<...>()` が消えていることを確認した。最後の blocker だった `type_ignore_from_import` は resolver が `main -> __pytra_main` rename を考慮して bare `Callable` を `callable[[],None]` に refine するよう修正し、`runtime_parity_check_fast --case-root fixture --targets cpp type_ignore_from_import` も `PASS` を確認した。sample broad parity の `18/18 PASS` と、直前の fixture broad parity `139/139 PASS` から、fresh probe の最終 blocker 解消をもって完了扱いとする。

**Phase 3: box/unbox 削除**

4. [x] [ID: P0-CPP-VARIANT-S8] C++ emitter の box/unbox 処理を削除し、variant 代入 / `std::get` に置換する
   - 完了メモ: fresh `parity-fast` の generated C++ entry `.cpp` では `.unbox<...>()` / `.as<...>()` は 0 件まで減っている。runtime EAST の stale も切り分けて `[src/runtime/east/utils/assertions.east](/workspace/Pytra/src/runtime/east/utils/assertions.east)` を canonical source に再同期した。さらに `[src/pytra/utils/assertions.py](/workspace/Pytra/src/pytra/utils/assertions.py)` の `py_assert_stdout` を `callable[[], None]` に上げたことで、fresh in-memory transpile では `_case_main` harness の `([&](object) -> object { ... })` bridge も消えている。fresh probe で残る `object` 経路は explicit bare `Callable` を `::std::function<object(object)>` に落としている `type_ignore_from_import` だけで、box/unbox 残件ではない。

**Phase 4: EAST から object 退化 / box / unbox を削除**

5. [x] [ID: P0-CPP-VARIANT-S10A] lower.py の non-explicit dynamic path から `resolved_type="object"` 生成を除去する
   - 完了メモ: C++ backend は `target_language="cpp"` では iter boundary lower を抑止して `py_iter_or_raise` / `py_next_or_stop` call をそのまま残す方針に固定した。さらに C++ 向け dynamic target `Box` では `resolved_type="object"` を固定せず target type を保持するようにし、代表ケースに対して `resolved_type="object"` が出ないことを `test_compile_uses_dynamic_target_resolved_type_for_cpp_box` / `test_compile_uses_union_target_resolved_type_for_cpp_box` / `test_compile_cpp_lowering_avoids_object_resolved_type_for_representative_dynamic_cases` で固定済み。fixture 全体を C++ 向けに lower して走査した結果、残る `resolved_type="object"` は `trait_basic`, `trait_with_inheritance`, `typed_container_access` の explicit dynamic/object 契約 6 ノードだけで、non-explicit dynamic path の残件は 0 を確認した。
6. [x] [ID: P0-CPP-VARIANT-S10B] iter boundary と explicit object / bare `Callable` 境界の残件を別契約として整理し、削除順を固定する
   - 完了メモ: C++ 向け lower の fixture 全走査を取り直し、non-explicit dynamic path の `resolved_type="object"` は 0、残件は `trait_basic`, `trait_with_inheritance`, `typed_container_access` の explicit object 契約 6 ノードだけであることを再確認した。あわせて iter boundary seam は旧 `iter_ops` ではなく `src/runtime/east/built_in/predicates.east` の generic `py_any` / `py_all` に残っていることを確認し、[p0-cpp-iter-boundary-runtime-contract.md](../plans/p0-cpp-iter-boundary-runtime-contract.md) を更新した。これにより `S10` 本体の残件は explicit object / bare `Callable` / runtime generic iter helper の 3 系統へ固定された。
7. [x] [ID: P0-CPP-VARIANT-S11] EAST3 validation に「`resolved_type: "object"` ならエラー」を追加する
   - 完了メモ: `toolchain2.compile.validate_east3` を新設し、`lower_east2_to_east3()` の終端で `resolved_type: "object"` を検出したら `RuntimeError` を投げるようにした。validator unit と `object` 注釈 source が compile で落ちる回帰を追加済み。
8. [ ] [ID: P0-CPP-VARIANT-S12] 全言語の fixture + sample が PASS することを確認する

### P20-CPP-SELFHOST: C++ emitter で toolchain2 を C++ に変換し g++ build を通す

文脈: [docs/ja/plans/p4-cpp-selfhost.md](../plans/p4-cpp-selfhost.md)

S0〜S4 完了済み（[archive/20260402.md](archive/20260402.md) 参照）。

1. [ ] [ID: P20-CPP-SELFHOST-S5] selfhost C++ バイナリを g++ でビルドし、リンクが通ることを確認する
2. [ ] [ID: P20-CPP-SELFHOST-S6] `run_selfhost_parity.py --selfhost-lang cpp --emit-target cpp --case-root fixture` で fixture parity が PASS することを確認する
3. [ ] [ID: P20-CPP-SELFHOST-S7] `run_selfhost_parity.py --selfhost-lang cpp --emit-target cpp --case-root sample` で sample parity が PASS することを確認する
