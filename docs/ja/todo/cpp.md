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

`_emit_constant` が `int64` 等の整数リテラルを常に `int64(0)` のようにキャスト付きで出力している（`emitter.py:1026-1027`）。C++ の整数リテラルは値に応じて `int` → `long` → `long long` と型が決まり、代入先の型に暗黙変換される。リテラル値が代入先の型の表現範囲内に収まる場合はキャスト不要。

判定基準: リテラル値が C++ の `int` 範囲（-2^31 〜 2^31-1）に収まり、かつ代入先の型が符号付き整数型（`int32`, `int64`）であればキャストを省略できる。以下はキャストが必要:
- `uint8`/`uint16`/`uint32`/`uint64` への代入（符号なし型への暗黙変換で意図しない promotion が起き得る）
- `int8`/`int16` への代入（narrowing conversion）
- `int` 範囲を超える大きなリテラル値

1. [ ] [ID: P0-CPP-LITERAL-S1] `_emit_constant` でリテラル値と代入先型を考慮し、安全な場合のみキャストを省略する
2. [ ] [ID: P0-CPP-LITERAL-S2] fixture + sample parity に影響がないことを確認する

### P5-CPP-PARENS: C++ emitter に演算子優先順位テーブルを追加する


1. [x] [ID: P5-CPP-PARENS-S1] C++ の演算子優先順位テーブルを定義し、CommonRenderer に渡す
   - 完了: `src/toolchain2/emit/profiles/cpp.json` に `operators.precedence` を追加し、`CommonRenderer` が profile から優先順位表を読み込んで `BinOp` / `UnaryOp` / `Compare` の括弧要否を判定するよう更新。C++ emitter はこの共通ロジックを使う形へ寄せ、`if ((count > 0))` のような冗長括弧を削減した
2. [x] [ID: P5-CPP-PARENS-S2] C++ fixture + sample parity に影響がないことを確認する
   - 完了: sample は `python3 tools/check/runtime_parity_check.py --targets cpp --case-root sample --east3-opt-level 2 --cpp-codegen-opt 3` で 18/18 PASS。fixture は `PYTHONPATH=src:tools python3 tools/check/runtime_parity_check_fast.py --targets cpp --case-root fixture --east3-opt-level 2` で `131 cases / 126 pass / 5 fail`。fail case は `any_none`, `integer_promotion`, `nested_closure_def`, `ok_generator_tuple_target`, `ok_typed_varargs_representative` の既知 5 件で、`docs/ja/progress/backend-progress-fixture.md` の C++ 赤ケースと一致し、新規 failure は増えていないことを確認

### P6-CPP-FIXPAR: fixture parity 失敗 5 件を解消する

文脈: [docs/ja/plans/p6-cpp-fixture-parity-failures.md](../plans/p6-cpp-fixture-parity-failures.md)

1. [ ] [ID: P6-CPP-FIXPAR-S1] `any_none` の `output mismatch` を解消する
2. [ ] [ID: P6-CPP-FIXPAR-S2] `integer_promotion` の `output mismatch` を解消する
3. [ ] [ID: P6-CPP-FIXPAR-S3] `nested_closure_def` の closure 参照解決を修正する
4. [ ] [ID: P6-CPP-FIXPAR-S4] `ok_generator_tuple_target` の `py_zip` / `py_sum` 再定義を解消する
5. [ ] [ID: P6-CPP-FIXPAR-S5] `ok_typed_varargs_representative` の const 修飾不整合を解消する

### P10-CPP-TYPETABLE-REDESIGN: g_type_table と destructor dispatch の再設計

`object.h` の `g_type_table[4096]` は RC のオブジェクト破棄時に destructor を呼ぶために使われている。isinstance の一本化（P3-CR-CPP-S6）とは別問題。`g_type_table` を撤去するには destructor dispatch の仕組みを再設計する必要がある。

1. [ ] [ID: P10-CPP-TYPETABLE-S1] `g_type_table` が destructor 以外にどこで使われているか棚卸しする
2. [ ] [ID: P10-CPP-TYPETABLE-S2] destructor dispatch を `g_type_table` なしで実現する設計を策定する（vtable、template 特殊化、`ControlBlock` に destructor ポインタを持たせる等）
3. [ ] [ID: P10-CPP-TYPETABLE-S3] `g_type_table`、`py_tid_register_known_class_type`、`PYTRA_TID_*` 定数を撤去する
4. [ ] [ID: P10-CPP-TYPETABLE-S4] fixture + sample parity に影響がないことを確認する

### P20-CPP-SELFHOST: C++ emitter で toolchain2 を C++ に変換し g++ build を通す

文脈: [docs/ja/plans/p4-cpp-selfhost.md](../plans/p4-cpp-selfhost.md)

1. [ ] [ID: P20-CPP-SELFHOST-S0] selfhost 対象コード（`src/toolchain2/` 全 .py）で戻り値型の注釈が欠けている関数に型注釈を追加する — resolve が `inference_failure` にならない状態にする（他言語と共通。先に完了した側の成果を共有）
2. [x] [ID: P20-CPP-SELFHOST-S1] toolchain2 全 .py を C++ に emit し、g++ build が通ることを確認する
   - 完了: code_emitter.py → code_emitter.cpp 生成・リンク成功（runtime cpp + 依存 .cpp と結合）
3. [x] [ID: P20-CPP-SELFHOST-S2] g++ build 失敗ケースを emitter/runtime の修正で解消する（EAST の workaround 禁止）
   - 完了: tuple subscript 検出拡張、py_dict_set_mut 追加、object→str/container 型強制、前方宣言二段階出力、is_simple_ident ガード、py_set_add_mut fallback を py_to_string 経由に変更
4. [ ] [ID: P20-CPP-SELFHOST-S3] selfhost 用 C++ golden を配置し、回帰テストとして維持する
