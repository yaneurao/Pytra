<a href="../../en/todo/rust.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — Rust backend

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-04-27

## 運用ルール

- **旧 toolchain1（`src/toolchain/emit/rs/`）は変更不可。** 新規開発・修正は全て `src/toolchain2/emit/rs/` で行う（[spec-emitter-guide.md](../spec/spec-emitter-guide.md) §1）。
- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度順（小さい P 番号から）に着手する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモを追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。
- **parity テストは「emit + compile + run + stdout 一致」を完了条件とする。**
- **[emitter 実装ガイドライン](../spec/spec-emitter-guide.md)を必ず読むこと。** parity check ツール、禁止事項、mapping.json の使い方が書いてある。

## 現状

- toolchain2 の Rust emitter は `src/toolchain2/emit/rs/` に実装済み（fixture 131/131 + sample 18/18 emit 成功）
- runtime は `src/runtime/rs/` に存在（toolchain2 向けに拡張中）
- compile + run parity は一部 fixture で PASS（class_instance, dataclass, class_tuple_assign, nested_types, str_index_char_compare 等）
- 残ブロッカー: 継承 + ref セマンティクスの EAST3 側問題（P0-EAST3-INHERIT）

## 未完了タスク

### P0-RS-FIXTURE-PARITY-161: Rust fixture parity を 161/161 に揃える

文脈: [docs/ja/plans/p0-fixture-parity-161.md](../plans/p0-fixture-parity-161.md)

現状: 151/161 PASS。FAIL: `collections/reversed_basic`, `imports/import_math_module`, `oop/trait_basic`, `oop/trait_with_inheritance`, `signature/ok_typed_varargs_representative`, `typing/optional_none`, `typing/union_basic`。未実行: `control/for_tuple_iter`, `typing/for_over_return_value`, `typing/nullable_dict_field`。

1. [x] [ID: P0-FIX161-RS-S1] 未実行 3 件を `runtime_parity_check_fast.py --targets rs --case-root fixture` で確定し、fail なら分類へ追加する
2. [x] [ID: P0-FIX161-RS-S2] `reversed_basic` / varargs / trait / optional / union / import runtime の fail を解消し、Rust fixture parity 161/161 PASS を確認する


### P1-HOST-CPP-EMITTER-RS: C++ emitter を rs で host する

C++ emitter（`toolchain.emit.cpp.cli`、16 モジュール）を rs に変換し、変換された emitter が C++ コードを正しく生成できることを確認する。C++ emitter の source は selfhost-safe 化済み。

1. [ ] [ID: P1-HOST-CPP-EMITTER-RS-S1] `python3 src/pytra-cli.py -build src/toolchain/emit/cpp/cli.py --target rs -o work/selfhost/host-cpp/rs/` で変換 + build を通す
2. [ ] [ID: P1-HOST-CPP-EMITTER-RS-S2] rs 版 C++ emitter で fixture manifest を処理し、Python 版 emitter と parity 一致を確認する

### P1-EMITTER-SELFHOST-RS: emit/rs/cli.py を単独で selfhost C++ build に通す

文脈: [docs/ja/plans/p1-emitter-selfhost-per-backend.md](../plans/p1-emitter-selfhost-per-backend.md)

各 backend emitter は subprocess で独立起動する自己完結プログラム。pytra-cli.py 全体の selfhost とは切り離し、`toolchain.emit.rs.cli` をエントリに単独で C++ build を通す。

1. [ ] [ID: P1-EMITTER-SELFHOST-RS-S1] `python3 src/pytra-cli.py -build src/toolchain/emit/rs/cli.py --target cpp -o work/selfhost/emit/rs/` を実行し、変換が通るようにする
2. [ ] [ID: P1-EMITTER-SELFHOST-RS-S2] 生成された C++ を `g++ -std=c++20 -O0` でコンパイルを通す（source 側の型注釈不整合を修正）
3. [ ] [ID: P1-EMITTER-SELFHOST-RS-S3] コンパイル済み emitter で既存 fixture の manifest を処理し、Python 版 emitter と parity 一致を確認する


### P0-RS-NEW-FIXTURE-PARITY: 新規追加 fixture / stdlib の parity 確認

今セッション（2026-04-01〜05）で追加・更新した fixture と stdlib の parity を確認する。

対象: `bytes_copy_semantics`, `negative_index_comprehensive`, `negative_index_out_of_range`, `callable_optional_none`, `str_find_index`, `eo_extern_opaque_basic`(emit-only), `math_extended`(stdlib), `os_glob_extended`(stdlib)

1. [x] [ID: P0-RS-NEWFIX-S1] 上記 fixture/stdlib の parity を確認する（対象 fixture のみ実行）
   - 完了: 2026-04-16 `runtime_parity_check_fast.py` で `bytes_copy_semantics` / `negative_index_comprehensive` / `negative_index_out_of_range` / `callable_optional_none` / `str_find_index` / `eo_extern_opaque_basic`(emit-only) / `math_extended` / `os_glob_extended` を再検証し、Rust で 8/8 PASS。`callable_optional_none` の optional callable 呼び出し描画と `math_native.rs` の `py_*` 互換エイリアスを修正。

### P9-RS-SELFHOST: Rust emitter で toolchain2 を Rust に変換し cargo build を通す

前提: P7-RS-EMITTER 完了後に着手。

1. [x] [ID: P9-RS-SELFHOST-S0] selfhost 対象コード（`src/toolchain2/` 全 .py）で戻り値型の注釈が欠けている関数に型注釈を追加する — resolve が `inference_failure` にならない状態にする（P4/P6/P20 と共通。先に完了した側の成果を共有）
   - 完了: `python3 -m unittest tools.unittest.selfhost.test_selfhost_return_annotations` で `src/toolchain2/` の戻り値注釈欠落が 0 件であることを確認。
2. [ ] [ID: P9-RS-SELFHOST-S1] flat `include!` を Rust `mod` + `use` 構造に置換する — 文脈: [plan-rs-selfhost-mod-structure.md](../plans/plan-rs-selfhost-mod-structure.md)
   - [ ] [ID: P9-RS-MOD-S1] Rust emitter の multifile_writer に mod 構造出力モードを追加する（1 EAST module = 1 Rust mod）
   - [ ] [ID: P9-RS-MOD-S2] `lib.rs` / `Cargo.toml` の自動生成を実装する
   - [ ] [ID: P9-RS-MOD-S3] cross-module `use crate::` パスの emit を実装する
3. [ ] [ID: P9-RS-SELFHOST-S2] toolchain2 全 .py を Rust に emit し、cargo build が通ることを確認する
4. [ ] [ID: P9-RS-SELFHOST-S3] cargo build 失敗ケースを emitter/runtime の修正で解消する（EAST の workaround 禁止）
5. [ ] [ID: P9-RS-SELFHOST-S4] selfhost 用 Rust golden を配置し、回帰テストとして維持する
6. [ ] [ID: P9-RS-SELFHOST-S5] `run_selfhost_parity.py --selfhost-lang rs --emit-target rs --case-root fixture` で fixture parity PASS
7. [ ] [ID: P9-RS-SELFHOST-S6] `run_selfhost_parity.py --selfhost-lang rs --emit-target rs --case-root sample` で sample parity PASS
