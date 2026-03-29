<a href="../../en/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO（未完了）

> `docs/ja/` が正（source of truth）です。`docs/en/` はその翻訳です。

最終更新: 2026-03-29

## 文脈運用ルール

- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 着手対象は「未完了の最上位優先度ID（最小 `P<number>`、同一優先度では上から先頭）」に固定し、明示上書き指示がない限り低優先度へ進まない。
- `P0` が 1 件でも未完了なら `P1` 以下には着手しない。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモ（件数等）を追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。
- **emitter の parity テストは「emit 成功」ではなく「emit + compile + run + stdout 一致」を完了条件とする。** emit だけ成功してもプレースホルダーコードが混入している可能性がある。

## 未完了タスク

### P0-FAST-PARITY-CPP-BUILD: 高速 parity check の C++ ビルドパスを修正する

文脈: [docs/ja/spec/spec-tools-parity.md](../spec/spec-tools-parity.md) §2

1. [ ] [ID: P0-FAST-PARITY-S1] `runtime_parity_check_fast.py` のインメモリ emit が生成する C++ ディレクトリ構成で、`type_id_table.h` 等の linker 生成ヘッダが正しく配置されるよう修正する
2. [ ] [ID: P0-FAST-PARITY-S2] `_run_cpp_emit_dir` の include パス（`-I`）が emit ディレクトリ構成と一致するよう調整する
3. [ ] [ID: P0-FAST-PARITY-S3] `runtime_parity_check_fast.py --category oop --targets cpp` で 18 件全件 PASS を確認する
4. [ ] [ID: P0-FAST-PARITY-S4] `runtime_parity_check_fast.py --targets cpp` で全 fixture の parity 結果が従来版（`runtime_parity_check.py`）と一致することを確認する

### P1-GO-CONTAINER-WRAPPER: Go emitter の container 既定表現を spec 準拠に修正する

文脈: `docs/ja/spec/spec-emitter-guide.md` §10

1. [ ] [ID: P1-GO-CONTAINER-S1] Go emitter の全コードパス（リテラル生成、関数引数、戻り値、ループ変数、代入等）で list/dict/set を既定で参照型ラッパー（`*PyList[T]`, `*PyDict[K,V]`, `*PySet[T]`）にする。値型（`[]T`, `map[K]V`）が混在している箇所を全て修正する
2. [ ] [ID: P1-GO-CONTAINER-S2] `meta.linked_program_v1.container_ownership_hints_v1.container_value_locals_v1` ヒントがある局所変数のみ値型縮退を許可する
3. [ ] [ID: P1-GO-CONTAINER-S3] Go runtime ヘルパー（`PyListConcat`, `PyListExtend` 等）が全て `*PyList[T]` を受け取る形に統一する
4. [ ] [ID: P1-GO-CONTAINER-S4] fixture 132 件 + sample 18 件の Go compile + run parity を通す

### P3-COMMON-RENDERER-CPP: C++ emitter の CommonRenderer 移行 + fixture parity

文脈: [docs/ja/plans/p2-lowering-profile-common-renderer.md](../plans/p2-lowering-profile-common-renderer.md)
仕様: [docs/ja/spec/spec-language-profile.md](../spec/spec-language-profile.md) §8

1. [ ] [ID: P3-CR-CPP-S1] C++ emitter を CommonRenderer + override 構成に移行する — `src/toolchain2/emit/profiles/cpp.json` のプロファイルに従い、CommonRenderer の共通ノード走査を使う構成にする。C++ 固有のノード（ClassDef, FunctionDef, ForCore, With 等）だけ override として残す
2. [ ] [ID: P3-CR-CPP-S2] fixture 132 件 + sample 18 件の C++ compile + run parity を通す
3. [ ] [ID: P3-CR-CPP-S3] C++ runtime の dict_ops.h インクルードガード外コードを修正する — タプル用 `py_at` の実装が `#endif` の外に置かれており、多重インクルードで再定義エラーになる
4. [ ] [ID: P3-CR-CPP-S4] C++ runtime の py_types.h 例外安全性を修正する — `PyBoxedValue` と `ControlBlock` の2段階 `new` で最初の確保後に例外が起きるとメモリリーク。`make_unique` 等で対処する
5. [ ] [ID: P3-CR-CPP-S5] CommonRenderer の list/dict/tuple 出力で `source_span.lineno` を参照し、元ソースの改行を再現する
6. [ ] [ID: P3-CR-CPP-S6] C++ runtime の旧 type_id ヘルパーを撤去する — `type_id_support.h` の `py_tid_is_subtype` / `py_tid_isinstance` / `py_runtime_value_type_id` 等の旧関数群、`object.h` の `g_type_table[4096]`、`PYTRA_TID_*` ハードコード定数を削除し、`pytra.built_in.type_id_table` の `pytra_isinstance` に一本化する — 現状の emitter は list リテラルを `", ".join(parts)` で1行に出力しており、元ソースの改行位置を無視している。前の要素と `source_span.lineno` が異なる場合に改行を入れる。synthetic module（type_id_table 等）は linker が適切な `source_span` を振ることで同じ仕組みで整形される

### P5-COMMON-RENDERER-GO: Go emitter の CommonRenderer 移行 + fixture parity

文脈: [docs/ja/plans/p2-lowering-profile-common-renderer.md](../plans/p2-lowering-profile-common-renderer.md)
仕様: [docs/ja/spec/spec-language-profile.md](../spec/spec-language-profile.md) §8

1. [ ] [ID: P5-CR-GO-S1] Go emitter を CommonRenderer + override 構成に移行する — `src/toolchain2/emit/profiles/go.json` のプロファイルに従い、CommonRenderer の共通ノード走査を使う構成にする。Go 固有のノード（FunctionDef のレシーバー、ForCore、multi_return 等）だけ override として残す
2. [ ] [ID: P5-CR-GO-S2] fixture 132 件 + sample 18 件の Go compile + run parity を通す

### P6-GO-SELFHOST: Go emitter で toolchain2 を Go に変換し go build を通す

前提: P1-GO-CONTAINER-WRAPPER 完了後に着手。

1. [ ] [ID: P6-GO-SELFHOST-S0] selfhost 対象コード（`src/toolchain2/` 全 .py）で戻り値型の注釈が欠けている関数に型注釈を追加する — resolve が `inference_failure` にならない状態にする
2. [ ] [ID: P6-GO-SELFHOST-S1] toolchain2 全 .py を Go に emit し、go build が通ることを確認する
2. [ ] [ID: P6-GO-SELFHOST-S2] go build 失敗ケースを emitter/runtime の修正で解消する（EAST の workaround 禁止）
3. [ ] [ID: P6-GO-SELFHOST-S3] selfhost 用 Go golden を配置し、回帰テストとして維持する

### P10-REORG: tools/ と test/unit/ の棚卸し・統合・管理台帳

文脈: [docs/ja/plans/p10-tools-test-reorg.md](../plans/p10-tools-test-reorg.md)

前提: P0〜P4 の主要タスクが全て落ち着いてから着手。

1. [ ] [ID: P10-REORG-S1] tools/ 全スクリプトの棚卸し
2. [ ] [ID: P10-REORG-S2] tools/check/, tools/gen/, tools/run/ にフォルダ分け
3. [ ] [ID: P10-REORG-S3] test/unit/ 全テストの棚卸し
4. [ ] [ID: P10-REORG-S4] test/unit/ → tools/unittest/ に統合・再編
5. [ ] [ID: P10-REORG-S5] 全パス参照の更新
6. [ ] [ID: P10-REORG-S6] tools/README.md 管理台帳を作成
7. [ ] [ID: P10-REORG-S7] CI で台帳突合チェックを追加
8. [ ] [ID: P10-REORG-S8] AGENTS.md にファイル追加禁止ルールを追加

### P11-VERSION-GATE: toolchain2 用バージョンチェッカーの新設

前提: toolchain2 への完全移行後に着手。

1. [ ] [ID: P11-VERGATE-S1] `src/toolchain2/` 向けの `transpiler_versions.json` を新設する（toolchain1 の `src/toolchain/misc/transpiler_versions.json` は廃止）
2. [ ] [ID: P11-VERGATE-S2] toolchain2 のディレクトリ構成に合わせた shared / 言語別の依存パスを定義する
3. [ ] [ID: P11-VERGATE-S3] バージョンチェッカーを新しく書く（PATCH 以上の bump で OK とする。MINOR/MAJOR はユーザーの明示指示がある場合のみ）
4. [ ] [ID: P11-VERGATE-S4] 旧チェッカー（`tools/check_transpiler_version_gate.py`）と旧バージョンファイルを廃止する

### P20-INT32: int のデフォルトサイズを int64 → int32 に変更

文脈: [docs/ja/plans/p4-int32-default.md](../plans/p4-int32-default.md)

前提: Go selfhost 完了後に着手。影響範囲が大きいため P4 → P20 に降格。

1. [ ] [ID: P20-INT32-S1] spec-east.md / spec-east2.md の `int` → `int32` 正規化ルール変更
2. [ ] [ID: P20-INT32-S2] resolve の型正規化を修正
3. [ ] [ID: P20-INT32-S3] sample 18 件のオーバーフロー確認 + 必要な箇所を `int64` に明示
4. [ ] [ID: P20-INT32-S4] golden 再生成 + 全 emitter parity 確認

注: 完了済みタスクは [アーカイブ](archive/index.md) に移動済み。
