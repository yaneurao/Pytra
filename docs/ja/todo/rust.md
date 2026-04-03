<a href="../../en/todo/rust.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — Rust backend

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-04-03

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

### P0-RS-TYPE-ID-CLEANUP: Rust runtime から PYTRA_TID_* / type_id テーブルを削除する

仕様: [docs/ja/spec/spec-adt.md](../spec/spec-adt.md) §6

Rust emitter が `instanceof` をネイティブ pattern match で処理するようになったら、runtime の `PYTRA_TID_*` 定数と type_id テーブルを削除する。

1. [x] [ID: P0-RS-TYPEID-CLN-S1] `src/runtime/rs/built_in/py_runtime.rs` から `PYTRA_TID_*` 定数と type_id テーブルを削除する
   - 完了: Rust runtime の `PYTRA_TID_*` / `PyTypeInfo` / `py_register_type_info` / `PyRuntimeTypeId` を削除し、`PyAny::TypeId` + `py_builtin_type_id_pyany` / `py_builtin_type_id_any` に置換。CLI/package emit でも type-id table を必要時のみ生成するように変更した。
2. [x] [ID: P0-RS-TYPEID-CLN-S2] `pytra_isinstance` / `py_is_subtype` を削除し、emitter は `match` / `if let` を使う
   - 完了: Rust emitter の user-class `isinstance` を `PyAny::TypeId` と downcast ベースへ移行し、`py_is_subtype` / `py_runtime_type_id` / `py_register_type_info` 依存を emit しない形に整理。`trait_basic`, `trait_with_inheritance`, `isinstance_user_class`, `class_inherit_basic`, `object_container_access` の Rust parity `5/5 PASS` を確認。
3. [x] [ID: P0-RS-TYPEID-CLN-S3] fixture + sample + stdlib parity に回帰がないことを確認する
   - 完了: Rust emitter/runtime の `json_*`, `optional_none`, `property_method_call`, `str_repr_containers`, `union_basic`, `union_dict_items` などの回帰を修正し、`runtime_parity_check_fast` で `stdlib 16/16 PASS`, `sample 18/18 PASS`, `fixture 145/145 PASS` を確認。

### P0-RS-OBJECT-CONTAINER: object_container_access fixture の Rust parity を通す

文脈: [docs/ja/plans/plan-object-container-access-parity.md](../plans/plan-object-container-access-parity.md)

selfhost で必要な動的型パターン（`dict[str, object]` の items() unpack / get()、`list[object]` の index、str 不要 unbox、`set[tuple[str,str]]`）を網羅する fixture。EAST3 には全て情報が載っている。

1. [x] [ID: P0-RS-OBJ-CONT-S1] `object_container_access` fixture が Rust で compile + run parity PASS することを確認する（失敗なら emitter を修正）
   - 完了: Rust emitter の generic method signature と union container (`dict[str, str | int]`, `list[int | str]`) の `PyAny` coercion を修正し、`runtime_parity_check_fast --case-root fixture --targets rs object_container_access` で PASS を確認。

### P0-RS-TUPLE-UNPACK: tuple_unpack_variants fixture の Rust parity を通す

文脈: [docs/ja/plans/plan-east-tuple-unpack-bugs.md](../plans/plan-east-tuple-unpack-bugs.md)

前提: P0-EAST-TUPLE-UNPACK（infra TODO）で EAST 側のバグ 3 件（括弧付き左辺、comprehension + unpack）が修正された後に着手。

1. [x] [ID: P0-RS-TUPLE-UNPACK-S1] `tuple_unpack_variants` fixture が Rust で compile + run parity PASS することを確認する（失敗なら emitter を修正）

### P0-RS-TYPED-CONTAINER: typed_container_access fixture の Rust parity を通す

文脈: [docs/ja/plans/plan-typed-container-access-parity.md](../plans/plan-typed-container-access-parity.md)

selfhost で必要な 4 パターン（dict.items() tuple unpack, typed dict.get(), typed list index, str cast）を網羅する fixture。EAST3 には全て情報が載っており、emitter が既存フィールドを正しく読めば解決する。

1. [x] [ID: P0-RS-TYPED-S1] `typed_container_access` fixture が Rust で compile + run parity PASS することを確認する（失敗なら emitter を修正）

### P0-LINKER-RECEIVER-HINT: linker に receiver_storage_hint を追加

文脈: [docs/ja/plans/plan-common-renderer-peer-class-info.md](../plans/plan-common-renderer-peer-class-info.md)

1. [x] S1〜S4 完了（linker pass 追加、Rust emitter borrow() 挿入、pathlib parity PASS）
2. [x] [ID: P0-RECV-HINT-S5] fixture + sample の全件 parity に回帰がないことを確認する

### P0-RS-SKIP-PURE-PY: skip_modules から pure Python モジュールを外す

`check_emitter_hardcode_lint.py --lang rs` で `skip_pure_python` 違反 2 件。`mapping.json` の `skip_modules` に `pytra.std.pathlib` と `pytra.std.env` が入っているが、両方とも `@extern` なしの pure Python モジュールであり transpile すべき。正本ソースに `@extern` マーカーを足して lint を黙らせるのは禁止。

1. [x] [ID: P0-RS-SKIP-PURE-S1] `src/runtime/rs/mapping.json` の `skip_modules` から `pytra.std.pathlib` と `pytra.std.env` を削除する
2. [x] [ID: P0-RS-SKIP-PURE-S2] transpile された pathlib / env が Rust で compile できることを確認する（必要なら emitter / runtime を修正）
3. [x] [ID: P0-RS-SKIP-PURE-S3] `check_emitter_hardcode_lint.py --lang rs` で `skip_pure_python` が 0 件になることを確認する
4. [x] [ID: P0-RS-SKIP-PURE-S4] fixture + sample parity に回帰がないことを確認する

### P5-RS-CLI-COMMON: Rust cli.py を共通ランナーに移行する

文脈: [docs/ja/plans/p5-rs-cli-common-runner.md](../plans/p5-rs-cli-common-runner.md)

全17言語中 Rust のみ独自 cli.py（235行）。type_id テーブル廃止（P0-RS-TYPEID-CLN）後に共通ランナーへ移行可能。

前提: P0-RS-TYPEID-CLN 完了（type_id テーブル不要化）

1. [x] [ID: P5-RS-CLI-S1] Rust emitter を `expected_type_name` ベースに移行する
   - 完了: Rust emitter の `isinstance` / class hierarchy 判定は `expected_type_name` fallback と `PyAny::TypeId` / downcast ベースに整理済みで、manifest type-id table を前提にしない形へ移行した。
2. [x] [ID: P5-RS-CLI-S2] `_generate_type_id_table_rs` と `_manifest_type_id_table` を削除する
   - 完了: [cli.py](../../src/toolchain2/emit/rs/cli.py) から Rust 独自の type-id table 生成を削除した。
3. [x] [ID: P5-RS-CLI-S3] runtime コピーと package mode を `post_emit` に移動し、共通ランナーに委譲する
   - 完了: Rust `cli.py` を `run_emit_cli(...)` ベースへ移行し、runtime コピーと `--package` の `Cargo.toml` / `src/lib.rs` / `src/main.rs` 生成を `post_emit` 側へ移した。`pytra-cli2 -build ... --target rs` と `--rs-package` の両方で emit 成功を確認。
4. [x] [ID: P5-RS-CLI-S4] Rust parity に回帰がないことを確認する
   - 完了: broad parity は `P0-RS-TYPEID-CLN-S3` で `stdlib 16/16 PASS`, `sample 18/18 PASS`, `fixture 145/145 PASS` を確認済み。CLI 共通化後も `runtime_parity_check_fast --case-root fixture --targets rs top_level union_basic optional_none` が `3/3 PASS` で、spot check に回帰がないことを確認。

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
