<a href="../../en/todo/cpp.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — C++ backend

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-03-31

## 運用ルール

- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度順（小さい P 番号から）に着手する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモを追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。
- **parity テストは「emit + compile + run + stdout 一致」を完了条件とする。**
- **[emitter 実装ガイドライン](../spec/spec-emitter-guide.md)を必ず読むこと。** parity check ツール、禁止事項、mapping.json の使い方が書いてある。

## 未完了タスク

### P0-CPP-LITERAL-CAST: 整数リテラルの冗長キャストを除去する

文脈: [docs/ja/plans/plan-cpp-literal-cast.md](../plans/plan-cpp-literal-cast.md)

`_emit_constant` が整数リテラルを常に `int64(0)` のようにキャスト付きで出力している。CommonRenderer に `literal_nowrap_ranges` テーブルを追加し、各言語共通で判定する仕組みにする。

1. [x] [ID: P0-CPP-LITERAL-S1] CommonRenderer に `literal_nowrap_ranges` テーブル読み込み + `render_constant` 拡張を実装する
   - 完了: `CommonRenderer` が profile の `literal_nowrap_ranges` を読み込み、整数 `Constant` を値域に応じて bare literal / typed wrap に分岐するよう更新した。`types` mapping も参照して `int64(2147483648)` のような fallback wrap を共通ロジックで生成する
2. [x] [ID: P0-CPP-LITERAL-S2] C++ の profile/mapping に `literal_nowrap_ranges` を設定し、`_emit_constant` の整数キャストロジックを CommonRenderer へ委譲する
   - 完了: `src/toolchain2/emit/profiles/cpp.json` に C++ 用の `literal_nowrap_ranges` を追加し、`_emit_constant` は整数型を `CommonRenderer.render_constant(...)` へ委譲する形へ縮退した。あわせて `min` / `max` は template deduction を壊さないよう integer literal を target type で強制ラップする補助経路を追加した
3. [x] [ID: P0-CPP-LITERAL-S3] fixture + sample parity に影響がないことを確認する
   - 完了: sample は `PYTHONPATH=src:tools python3 tools/check/runtime_parity_check_fast.py --targets cpp --case-root sample --east3-opt-level 2` で `18/18 PASS` を確認。fixture は直前の full run が `130/131` で唯一の失敗だった `exception_user_defined_multi_handler` を修正し、`runtime_parity_check_fast.py ... exception_user_defined_multi_handler` と `... super_init` の個別 PASS、加えて `src/pytra-cli.py build test/fixture/source/py/control/exception_user_defined_multi_handler.py --target cpp` の build 成功を確認した

### P5-CPP-PARENS: C++ emitter に演算子優先順位テーブルを追加する


1. [x] [ID: P5-CPP-PARENS-S1] C++ の演算子優先順位テーブルを定義し、CommonRenderer に渡す
   - 完了: `src/toolchain2/emit/profiles/cpp.json` に `operators.precedence` を追加し、`CommonRenderer` が profile から優先順位表を読み込んで `BinOp` / `UnaryOp` / `Compare` の括弧要否を判定するよう更新。C++ emitter はこの共通ロジックを使う形へ寄せ、`if ((count > 0))` のような冗長括弧を削減した
2. [x] [ID: P5-CPP-PARENS-S2] C++ fixture + sample parity に影響がないことを確認する
   - 完了: sample は `python3 tools/check/runtime_parity_check.py --targets cpp --case-root sample --east3-opt-level 2 --cpp-codegen-opt 3` で 18/18 PASS。fixture は `PYTHONPATH=src:tools python3 tools/check/runtime_parity_check_fast.py --targets cpp --case-root fixture --east3-opt-level 2` で `131 cases / 126 pass / 5 fail`。fail case は `any_none`, `integer_promotion`, `nested_closure_def`, `ok_generator_tuple_target`, `ok_typed_varargs_representative` の既知 5 件で、`docs/ja/progress/backend-progress-fixture.md` の C++ 赤ケースと一致し、新規 failure は増えていないことを確認

### P6-CPP-FIXPAR: fixture parity 失敗 5 件を解消する

文脈: [docs/ja/plans/p6-cpp-fixture-parity-failures.md](../plans/p6-cpp-fixture-parity-failures.md)

1. [x] [ID: P6-CPP-FIXPAR-S1] `any_none` の `output mismatch` を解消する
   - 完了: `is None` / `is not None` の C++ emit を `py_is_none(...)` ベースへ修正し、`PYTHONPATH=src:tools python3 tools/check/runtime_parity_check_fast.py --targets cpp --case-root fixture --east3-opt-level 2 any_none` で PASS を確認
2. [x] [ID: P6-CPP-FIXPAR-S2] `integer_promotion` の `output mismatch` を解消する
   - 完了: stale な integer `numeric_promotion` cast を C++ emitter 側で無視し、`PYTHONPATH=src:tools python3 tools/check/runtime_parity_check_fast.py --targets cpp --case-root fixture --east3-opt-level 2 integer_promotion` で PASS を確認
3. [x] [ID: P6-CPP-FIXPAR-S3] `nested_closure_def` の closure 参照解決を修正する
   - 完了: local closure 名を visible local scope に登録し、再帰 closure と sibling closure 呼び出しで `::rec` / `::inner` を出さないよう修正。`runtime_parity_check_fast.py ... nested_closure_def` で PASS を確認
4. [x] [ID: P6-CPP-FIXPAR-S4] `ok_generator_tuple_target` の `py_zip` / `py_sum` 再定義を解消する
   - 完了: `src/runtime/cpp/built_in/zip_ops.h` を `list_ops.h` への互換 shim に変更し、重複定義を解消。`runtime_parity_check_fast.py ... ok_generator_tuple_target` で PASS を確認
5. [x] [ID: P6-CPP-FIXPAR-S5] `ok_typed_varargs_representative` の const 修飾不整合を解消する
   - 完了: call graph を見て mutable param を signature へ反映するよう C++ emitter を補正し、`runtime_parity_check_fast.py ... ok_typed_varargs_representative` で PASS を確認

### P10-CPP-TYPETABLE-REDESIGN: g_type_table と destructor dispatch の再設計

文脈: [docs/ja/plans/p10-cpp-typetable-redesign.md](../plans/p10-cpp-typetable-redesign.md)

`object.h` の `g_type_table[4096]` は RC のオブジェクト破棄時に destructor を呼ぶために使われている。isinstance の一本化（P3-CR-CPP-S6）とは別問題。`g_type_table` を撤去するには destructor dispatch の仕組みを再設計する必要がある。

1. [x] [ID: P10-CPP-TYPETABLE-S1] `g_type_table` が destructor 以外にどこで使われているか棚卸しする
   - 完了: 実利用は `Object<T>::release()` / `Object<void>::release()` の destructor dispatch と C++ unit test の初期化だけで、toolchain2 の user class subtype 判定は generated `built_in/type_id.*` の `id_table` と `py_runtime_object_type_id(...)` で完結していることを確認
2. [x] [ID: P10-CPP-TYPETABLE-S2] destructor dispatch を `g_type_table` なしで実現する設計を策定する（vtable、template 特殊化、`ControlBlock` に destructor ポインタを持たせる等）
   - 完了: `ControlBlock` に `void (*deleter)(void*)` を保持し、`make_object<T>` と POD boxing constructor が concrete deleter を焼き込む設計へ変更。release 時は `cb->deleter` を直接呼ぶ形にした
3. [x] [ID: P10-CPP-TYPETABLE-S3] `g_type_table` と `py_tid_register_known_class_type` を撤去し、built-in `PYTRA_TID_*` 定数は維持対象として整理する
   - 完了: `src/runtime/cpp/core/object.h` から `g_type_table` 参照を撤去し、`src/toolchain2/emit/cpp/emitter.py` から local `py_tid_register_known_class_type(...)` helper を撤去。`src/pytra/built_in/type_id.py` と再生成した `src/runtime/east/built_in/type_id.east` から known-registration API を削除した。`PYTRA_TID_*` は built-in scalar/container/object の runtime 定数として広く使われるため撤去対象外と明記
4. [x] [ID: P10-CPP-TYPETABLE-S4] fixture + sample parity に影響がないことを確認する
   - 完了: `PYTHONPATH=src:tools python3 tools/check/runtime_parity_check_fast.py --targets cpp --case-root fixture --east3-opt-level 2` で `131/131 PASS`、`PYTHONPATH=src:tools python3 tools/check/runtime_parity_check_fast.py --targets cpp --case-root sample --east3-opt-level 2` で `18/18 PASS` を確認

### P20-CPP-SELFHOST: C++ emitter で toolchain2 を C++ に変換し g++ build を通す

文脈: [docs/ja/plans/p4-cpp-selfhost.md](../plans/p4-cpp-selfhost.md)

1. [x] [ID: P20-CPP-SELFHOST-S0] selfhost 対象コード（`src/toolchain2/` 全 .py）で戻り値型の注釈が欠けている関数に型注釈を追加する — resolve が `inference_failure` にならない状態にする（他言語と共通。先に完了した側の成果を共有）
   - 完了: `ast` 走査で `src/toolchain2/` 全 `.py` の `FunctionDef` / `AsyncFunctionDef` を監査し、戻り値注釈欠落が 0 件であることを確認。回帰防止として `tools/unittest/selfhost/test_selfhost_return_annotations.py` を追加した
2. [x] [ID: P20-CPP-SELFHOST-S1] toolchain2 全 .py を C++ に emit し、g++ build が通ることを確認する
   - 完了: code_emitter.py → code_emitter.cpp 生成・リンク成功（runtime cpp + 依存 .cpp と結合）
3. [x] [ID: P20-CPP-SELFHOST-S2] g++ build 失敗ケースを emitter/runtime の修正で解消する（EAST の workaround 禁止）
   - 完了: tuple subscript 検出拡張、py_dict_set_mut 追加、object→str/container 型強制、前方宣言二段階出力、is_simple_ident ガード、py_set_add_mut fallback を py_to_string 経由に変更
4. [ ] [ID: P20-CPP-SELFHOST-S3] selfhost 用 C++ golden を配置し、回帰テストとして維持する
