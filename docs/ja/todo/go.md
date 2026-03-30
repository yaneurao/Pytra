<a href="../../en/todo/go.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — Go backend

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-03-30

## 運用ルール

- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度順（小さい P 番号から）に着手する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモを追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。
- **parity テストは「emit + compile + run + stdout 一致」を完了条件とする。**
- **[emitter 実装ガイドライン](../spec/spec-emitter-guide.md)を必ず読むこと。** parity check ツール、禁止事項、mapping.json の使い方が書いてある。

## 未完了タスク

### P0-GO-BOOLOP-BOOL-SHORTCIRCUIT: bool 型の and/or を && / || で出力する

`if t > 0.0 and t < t_min:` のように両辺が比較式で期待型が `bool` の場合、Go では `if t > 0.0 && t < t_min {` と出力すべき。現状は値選択式として即時実行クロージャに展開しており、コードが著しく読みにくい。

spec-east.md §7: 「期待型が `bool` のときは真偽演算（`&&`/`||`）として出力する。期待型が `bool` 以外のときは値選択式として出力する。」

1. [x] [ID: P0-GO-BOOLOP-S1] Go emitter の BoolOp emit で、`resolved_type` が `bool` の場合は `&&` / `||` で出力するよう修正する
2. [x] [ID: P0-GO-BOOLOP-S2] `boolop_value_select` fixture + sample 02/全件で Go parity PASS を確認する — typing 23/23, stdlib 16/16, sample 02 PASS

### P0-GO-TUPLE-MULTIRETURN: tuple multi-return 展開の不完全さを修正する

Review 指摘: `py_splitext` を多値返却にした後、emitter の `_emit_assign`（`emitter.py:3780`）は `tuple[...] = Call(...)` を `name_0, name_1 := ...` に展開するが、元の `name` 自体は束縛しないため `return name` / `f(name)` が未定義参照になる。さらに `_emit_subscript`（`emitter.py:2915`）は `ctx.tup_multi_vars` に載った Name しか救済しないため、`os.path.splitext(p)[0]` のような直接添字が不正コードになる。

1. [x] [ID: P0-GO-TUPLE-MR-S1] tuple multi-return 展開で元の変数名も束縛するか、直接添字（`Call(...)[0]`）を multi-return の要素選択として emit する — `Call(...)[i]` を IIFE で展開する実装を追加
2. [x] [ID: P0-GO-TUPLE-MR-S2] `os_glob_extended` / `pathlib_extended` fixture が Go で compile + run parity PASS することを確認する — stdlib 4件・typing 23/23 PASS

### P0-RESOLVE-INT-PROMOTION: BinOp の全演算子で整数昇格 cast がオペランドに付くよう修正する

全ての BinOp（`+`, `-`, `*`, `/`, `//`, `%`, `&`, `|`, `^`, `<<`, `>>`）で、異なるサイズの整数型が混在する場合に、resolve が **演算の前に** 両オペランドを結果型に cast すべき。現状は小さい側を相手のサイズに cast するだけで、結果型への昇格 cast が付かない。Go/Rust は暗黙昇格がないのでコンパイルエラーになる。

例: `m8: int8 = 100; m16: int16 = 100; r5: int32 = m8 * m16`
- NG: `int16(m8) * m16` → 結果は int16（overflow あり）、int32 への cast なし
- OK: `int32(m8) * int32(m16)` → 結果は int32、overflow なし

1. [x] [ID: P0-RESOLVE-INTPROMO-S1] resolve の BinOp 整数昇格で、全演算子について cast を「結果型にまで昇格」に修正する — 両オペランドに結果型への cast を付ける
2. [x] [ID: P0-RESOLVE-INTPROMO-S2] `integer_promotion` fixture が Go で compile + run parity PASS することを確認する
3. [x] [ID: P0-RESOLVE-INTPROMO-S3] 他の fixture に影響がないことを確認する（golden 再生成）— typing 23/23, stdlib 16/16, sample 18/18 全 PASS

### P2-COMMON-RENDERER-PARENS: CommonRenderer に演算子優先順位ベースの括弧制御を実装する

仕様: [spec-emitter-guide.md](../spec/spec-emitter-guide.md) §1.4

1. [x] [ID: P2-CR-PARENS-S1] CommonRenderer に演算子優先順位テーブルを受け取る仕組みを追加する — 各言語の emitter が自分の優先順位テーブルを渡す。Go の優先順位テーブルをプロトタイプとして最初に実装する
2. [x] [ID: P2-CR-PARENS-S2] BinOp / UnaryOp / Compare の出力時に「親の優先順位 ≥ 子の優先順位なら括弧を付ける」ロジックを実装する — 不要な括弧を出力しない
3. [x] [ID: P2-CR-PARENS-S3] 最外の冗長括弧（`x = (expr);` の外側）を除去する
4. [x] [ID: P2-CR-PARENS-S4] Go fixture + sample parity に影響がないことを確認する — typing 23/23, stdlib 16/16, sample 18/18 全 PASS

### P6-GO-SELFHOST: Go emitter で toolchain2 を Go に変換し go build を通す

前提: P1-GO-CONTAINER-WRAPPER 完了後に着手。

1. [ ] [ID: P6-GO-SELFHOST-S0] selfhost 対象コード（`src/toolchain2/` 全 .py）で戻り値型の注釈が欠けている関数に型注釈を追加する — resolve が `inference_failure` にならない状態にする
2. [ ] [ID: P6-GO-SELFHOST-S1] toolchain2 全 .py を Go に emit し、go build が通ることを確認する
3. [ ] [ID: P6-GO-SELFHOST-S2] go build 失敗ケースを emitter/runtime の修正で解消する（EAST の workaround 禁止）
4. [ ] [ID: P6-GO-SELFHOST-S3] selfhost 用 Go golden を配置し、回帰テストとして維持する
