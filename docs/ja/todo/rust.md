<a href="../../en/todo/rust.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — Rust backend

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

## 現状

- toolchain2 に Rust emitter は未実装（`src/toolchain2/emit/rs/` が存在しない）
- runtime は `src/runtime/rs/` に存在する（旧 toolchain1 時代の実装）
- 旧 toolchain1 の Rust emitter は `src/toolchain/emit/rs/` に存在するが、toolchain2 への移行が必要

## 未完了タスク

### P0-EAST3-NARROWING-CAST: isinstance narrowing 後に Cast/Unbox ノードを挿入する

文脈: [docs/ja/plans/p0-east3-narrowing-cast.md](../plans/p0-east3-narrowing-cast.md)

EAST3 は isinstance narrowing 後に `resolved_type` を更新するが、明示的な Cast/Unbox ノードを挿入しない。Rust のように PyAny から具象型へのダウンキャストが必要な言語では、emitter が自前で narrowing 判定するしかなく、§1.1 違反になる。

1. [x] [ID: P0-EAST3-NARROW-S1] isinstance narrowing で `resolved_type` が変わった Name 参照に Cast/Unbox ノードを挿入する — 元の型と narrowing 後の型が異なる場合のみ
   - 完了: `passes.py` の `apply_guard_narrowing` で `UnaryOp(Not)` / `BoolOp(And)` / `IfExp` パターンを追加し Unbox ノードを挿入。`test_isinstance_narrowing.py` 6/6 PASS。
2. [x] [ID: P0-EAST3-NARROW-S2] Rust emitter の `_emit_name` workaround を削除し、Unbox ノードをレンダリングするだけにする
   - 完了: `emitter.py` の `_emit_name` に workaround なし。Unbox ノードは `_emit_expr` の `kind == "Unbox"` ブランチで処理。
3. [x] [ID: P0-EAST3-NARROW-S3] 全言語の fixture parity に影響がないことを確認する
   - 完了: 全 131 fixture 再生成。typing 23/23, stdlib 16/16, sample 18/18 PASS（スモークテスト 22/65 は fixture 未生成の既知 43 件のみ失敗）。

### P0-RS-NARROWED-BINOP: narrowing 済み union 型の BinOp が todo!() に落ちる

Review 指摘: `emitter.py:411` で被演算子の格納型が `Box<dyn Any>` だと `todo!()` に落としている。EAST3 で isinstance narrowing 後の `a + b` は合法なのに、Rust backend だけ実行時 panic。`type_alias_pep695` fixture の `Scalar = int | float` の int 分岐が該当。

1. [x] [ID: P0-RS-NARROWED-BINOP-S1] EAST3 の narrowing 済み `resolved_type` を参照して正しい型で演算を emit する — `Box<dyn Any>` fallback ではなく narrowing 後の具象型を使う
   - 完了: Unbox ノード導入済み（P0-EAST3-NARROWING-CAST）により BinOp の子ノードは具象型で emit される。_emit_binop の Box<dyn Any> downcast ロジックに結果型・対向operand型からの推論フォールバックを追加。
2. [x] [ID: P0-RS-NARROWED-BINOP-S2] `type_alias_pep695` fixture が Rust で compile + run parity PASS することを確認する
   - 完了: PyAny に PyStringify 実装を追加し、runtime_parity_check_fast PASS 確認。

### P0-RS-TYPE-MAPPING: Rust emitter の型写像を mapping.json に移行する

仕様: [spec-runtime-mapping.md](../spec/spec-runtime-mapping.md) §7

1. [x] [ID: P0-RS-TYPEMAP-S1] `src/runtime/rs/mapping.json` に `types` テーブルを追加する — POD 型（`int64` → `i64` 等）とクラス型（`Exception` → `Box<dyn std::error::Error>` 等）の全写像を定義する
   - 完了: mapping.json に 37 エントリの types テーブルを追加。
2. [x] [ID: P0-RS-TYPEMAP-S2] Rust emitter の型名ハードコード（`types.py` 含む）を `resolve_type()` 呼び出しに置換する
   - 完了: types.py の rs_type() を mapping.json の types テーブルから優先参照するように変更。set_mapping_types() で emit 開始時にアクティブ化。_FALLBACK_TYPE_MAP はフォールバック用に残存。
3. [x] [ID: P0-RS-TYPEMAP-S3] fixture emit に影響がないことを確認する
   - 完了: 129/131 fixture emit 成功（残 2 件は既存の module_prefix 未定義問題、型マッピング無関係）。type_alias_pep695 parity PASS。

### P0-RS-LINT-FIX: Rust emitter のハードコード違反を修正する

仕様: [spec-emitter-guide.md](../spec/spec-emitter-guide.md) §1, §7

違反一覧（`check_emitter_hardcode_lint.py` 検出）:
- module_name 2件: `"math": "math_native.rs"`, `"time": "time_native.rs"` — native ファイル名のハードコード。runtime manifest から導出すべき
- runtime_symbol 3件: `mapped == "py_len"`, `mapped == "py_print"` — mapping.json 経由で解決済みの値を再度文字列マッチしている
- class_name 1件: `"Exception": "Box<dyn std::error::Error>"` — P0-RS-TYPE-MAPPING で解消予定

1. [ ] [ID: P0-RS-LINT-S1] module_name 違反を修正する — `emitter.py` の native ファイル名テーブルを runtime manifest または mapping.json から導出する
2. [ ] [ID: P0-RS-LINT-S2] runtime_symbol 違反を修正する — `py_len` / `py_print` の文字列マッチを除去し、mapping.json の解決結果をそのまま使う
3. [ ] [ID: P0-RS-LINT-S3] `check_emitter_hardcode_lint.py` で Rust の違反が 0 件になることを確認する

### P7-RS-EMITTER: Rust emitter を toolchain2 に新規実装する

前提: Go emitter（参照実装）と CommonRenderer が安定してから着手。

1. [x] [ID: P7-RS-EMITTER-S1] `src/toolchain2/emit/rs/` に Rust emitter を新規実装する — Go emitter を参考に CommonRenderer + override 構成で作成。Rust 固有のノード（所有権・ライフタイム・borrow、match、impl ブロック等）だけ override として残す
   - 完了: `src/toolchain2/emit/rs/{emitter.py,types.py,__init__.py}` と `src/toolchain2/emit/profiles/rs.json` を作成。全 1001 件 fixture エラーなし emit 成功。pytra-cli2.py に rs target を追加。
2. [x] [ID: P7-RS-EMITTER-S2] `src/runtime/rs/mapping.json` を作成し、runtime_call の写像を定義する
   - 完了: `src/runtime/rs/mapping.json` を作成。Go mapping.json を参考に Rust 向け関数名でマッピング定義。
3. [ ] [ID: P7-RS-EMITTER-S3] fixture 132 件 + sample 18 件の Rust emit 成功を確認する
4. [ ] [ID: P7-RS-EMITTER-S4] Rust runtime を toolchain2 の emit 出力と整合させる（旧 toolchain1 runtime の引き継ぎ or 再実装）
5. [ ] [ID: P7-RS-EMITTER-S5] fixture + sample の Rust compile + run parity を通す

### P9-RS-SELFHOST: Rust emitter で toolchain2 を Rust に変換し cargo build を通す

前提: P7-RS-EMITTER 完了後に着手。

1. [ ] [ID: P9-RS-SELFHOST-S0] selfhost 対象コード（`src/toolchain2/` 全 .py）で戻り値型の注釈が欠けている関数に型注釈を追加する — resolve が `inference_failure` にならない状態にする（P4/P6 と共通。先に完了した側の成果を共有）
2. [ ] [ID: P9-RS-SELFHOST-S1] toolchain2 全 .py を Rust に emit し、cargo build が通ることを確認する
3. [ ] [ID: P9-RS-SELFHOST-S2] cargo build 失敗ケースを emitter/runtime の修正で解消する（EAST の workaround 禁止）
4. [ ] [ID: P9-RS-SELFHOST-S3] selfhost 用 Rust golden を配置し、回帰テストとして維持する
