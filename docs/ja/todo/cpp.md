<a href="../../en/todo/cpp.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — C++ backend

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-03-29

## 運用ルール

- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度順（小さい P 番号から）に着手する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモを追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。
- **parity テストは「emit + compile + run + stdout 一致」を完了条件とする。**
- **[emitter 実装ガイドライン](../spec/spec-emitter-guide.md)を必ず読むこと。** parity check ツール、禁止事項、mapping.json の使い方が書いてある。

## 未完了タスク

### P0-CPP-TYPE-MAPPING: C++ emitter の型写像を mapping.json に移行する

仕様: [spec-runtime-mapping.md](../spec/spec-runtime-mapping.md) §7

1. [ ] [ID: P0-CPP-TYPEMAP-S1] `src/runtime/cpp/mapping.json` に `types` テーブルを追加する — POD 型（`int64` → `int64_t` 等）とクラス型（`Exception` → `std::runtime_error` 等）の全写像を定義する
2. [ ] [ID: P0-CPP-TYPEMAP-S2] `CodeEmitter` 基底クラスに `resolve_type()` メソッドを追加する — `types` テーブルから型名を解決する共通 API
3. [ ] [ID: P0-CPP-TYPEMAP-S3] C++ emitter の型名ハードコード（`types.py` 含む）を `resolve_type()` 呼び出しに置換する
4. [ ] [ID: P0-CPP-TYPEMAP-S4] fixture parity に影響がないことを確認する

### P3-COMMON-RENDERER-CPP: C++ emitter の CommonRenderer 移行 + fixture parity

文脈: [docs/ja/plans/p2-lowering-profile-common-renderer.md](../plans/p2-lowering-profile-common-renderer.md)
仕様: [docs/ja/spec/spec-language-profile.md](../spec/spec-language-profile.md) §8

1. [ ] [ID: P3-CR-CPP-S1] C++ emitter を CommonRenderer + override 構成に移行する — `src/toolchain2/emit/profiles/cpp.json` のプロファイルに従い、CommonRenderer の共通ノード走査を使う構成にする。C++ 固有のノード（ClassDef, FunctionDef, ForCore, With 等）だけ override として残す
2. [x] [ID: P3-CR-CPP-S2] fixture 132 件 + sample 18 件の C++ compile + run parity を通す — oop 18/18, typing 22/22, signature 13/13 (うち stdlib の一部は複雑な依存のため残)
3. [x] [ID: P3-CR-CPP-S3] C++ runtime の dict_ops.h インクルードガード外コードを修正する — タプル用 `py_at` の実装が `#endif` の外に置かれており、多重インクルードで再定義エラーになる
   - 完了: commit 51447a04f — `py_at` for tuple を `#endif` の内側に移動
4. [x] [ID: P3-CR-CPP-S4] C++ runtime の py_types.h 例外安全性を修正する — `PyBoxedValue` と `ControlBlock` の2段階 `new` で例外安全にする。実用上 bad_alloc はリカバー不可能だが、変換器が生成するコードの品質として例外安全を保証する
   - 完了: commit 678317b7e / 51447a04f — `make_unique` に移行
5. [ ] [ID: P3-CR-CPP-S5] CommonRenderer の list/dict/tuple 出力で `source_span.lineno` を参照し、元ソースの改行を再現する
6. [ ] [ID: P3-CR-CPP-S6] C++ runtime の旧 type_id ヘルパーを撤去する — `type_id_support.h` の `py_tid_is_subtype` / `py_tid_isinstance` / `py_runtime_value_type_id` 等の旧関数群、`object.h` の `g_type_table[4096]`、`PYTRA_TID_*` ハードコード定数を削除し、`pytra.built_in.type_id_table` の `pytra_isinstance` に一本化する — 現状の emitter は list リテラルを `", ".join(parts)` で1行に出力しており、元ソースの改行位置を無視している。前の要素と `source_span.lineno` が異なる場合に改行を入れる。synthetic module（type_id_table 等）は linker が適切な `source_span` を振ることで同じ仕組みで整形される
7. [ ] [ID: P3-CR-CPP-S7] `rc_list_from_value` / `rc_dict_from_value` 等の型別 RC 化関数を汎用 `rc_from_value<T>` に一本化する — emitter は「非 POD → `rc_from_value(...)` で包む」だけで済むようにし、型ごとの関数名分岐を emitter から除去する
8. [x] [ID: P3-CR-CPP-S8] C++ emitter に `_safe_cpp_ident` を追加する — C++ 予約語（`double`, `class`, `int`, `float`, `namespace`, `template` 等）と衝突する関数名・メソッド名・変数名に末尾 `_` を付与する（Go emitter の `_safe_go_ident` と同等）

### P4-CPP-SELFHOST: C++ emitter で toolchain2 を C++ に変換し g++ build を通す

前提: P3-COMMON-RENDERER-CPP 完了後に着手。

1. [ ] [ID: P4-CPP-SELFHOST-S0] selfhost 対象コード（`src/toolchain2/` 全 .py）で戻り値型の注釈が欠けている関数に型注釈を追加する — resolve が `inference_failure` にならない状態にする（P6-GO-SELFHOST-S0 と共通。先に完了した側の成果を共有）
2. [ ] [ID: P4-CPP-SELFHOST-S1] toolchain2 全 .py を C++ に emit し、g++ build が通ることを確認する
3. [ ] [ID: P4-CPP-SELFHOST-S2] g++ build 失敗ケースを emitter/runtime の修正で解消する（EAST の workaround 禁止）
4. [ ] [ID: P4-CPP-SELFHOST-S3] selfhost 用 C++ golden を配置し、回帰テストとして維持する
