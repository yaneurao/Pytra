<a href="../../en/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO（未完了）

> `docs/ja/` が正（source of truth）です。`docs/en/` はその翻訳です。

最終更新: 2026-03-27

## 文脈運用ルール

- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 着手対象は「未完了の最上位優先度ID（最小 `P<number>`、同一優先度では上から先頭）」に固定し、明示上書き指示がない限り低優先度へ進まない。
- `P0` が 1 件でも未完了なら `P1` 以下には着手しない。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモ（件数等）を追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。
- **emitter の parity テストは「emit 成功」ではなく「emit + compile + run + stdout 一致」を完了条件とする。** emit だけ成功してもプレースホルダーコードが混入している可能性がある。

## 未完了タスク

### P0-TYPE-ID-TABLE: linker による type_id テーブル仮想モジュール生成

文脈: [docs/ja/plans/p0-type-id-table.md](../plans/p0-type-id-table.md)
仕様: [docs/ja/spec/spec-type_id.md](../spec/spec-type_id.md) §7、[docs/ja/spec/spec-linker.md](../spec/spec-linker.md) §6.4

1. [x] [ID: P0-TID-TABLE-S1] `pytra/built_in/` に `pytra_isinstance` 関数を pure Python で定義する
2. [x] [ID: P0-TID-TABLE-S2] linker に `pytra.built_in.type_id_table` 仮想モジュール生成を実装する（`id_table: list[int]` + TID 定数）
3. [x] [ID: P0-TID-TABLE-S3] linker が isinstance lower 時に対象モジュールへ import binding を挿入する
4. [x] [ID: P0-TID-TABLE-S4] C++ runtime の `g_type_table[4096]` ハードコードを撤廃する
5. [x] [ID: P0-TID-TABLE-S5] Go runtime の手書き TID 定数を撤廃する
6. [x] [ID: P0-TID-TABLE-S6] fixture + sample の C++/Go parity 確認 — linker focused regression 3 件追加、Go fixture `exception_propagation_two_frames.py` は `pytra-cli2 -build` + `go build && ./app.out` で `caught boom`、C++ は clean emit で helper `built_in/type_id_table.h/.cpp` まで出力確認

### P2-SELFHOST: toolchain2 自身の変換テスト

文脈: `docs/ja/plans/plan-pipeline-redesign.md` §3.5

1. [x] [ID: P2-SELFHOST-S1] `src/toolchain2/` の全 .py が parse 成功 — 37/46（9件は ParseContext再帰/Union forward ref/walrus等の parser未対応構文）
2. [x] [ID: P2-SELFHOST-S2] parse → resolve → compile → optimize まで通す — 37/37 全段通過
3. [x] [ID: P2-SELFHOST-S3] golden を `test/selfhost/` に配置し、回帰テストとして維持 — east1/east2/east3/east3-opt 各 37 件
4. [ ] [ID: P2-SELFHOST-S4] Go emitter で toolchain2 を Go に変換し、`go build` が通る — emit 25/25 成功、`go build` は docstring/構文問題で未達
5. [x] [ID: P2-SELFHOST-S5] Go emitter の unsupported expr/stmt を fail-fast に変更し、プレースホルダ出力を禁止する — `nil /* unsupported */` / `// unsupported stmt` を廃止し、spec-emitter-guide.md の fail-closed 契約に合わせる（Go focused regression 2 件追加）
6. [x] [ID: P2-SELFHOST-S6] Go emitter が `yields_dynamic` を正本として container getter/pop の型アサーションを判断するよう修正する — `resolved_type` / owner 文字列ベースの分岐をやめ、`Call.yields_dynamic` を使用（Go focused regression 2 件追加）
7. [ ] [ID: P2-SELFHOST-S7] Go emitter の container 既定表現を spec 準拠に修正する — list/dict/set を既定で参照型ラッパーにし、`meta.linked_program_v1.container_ownership_hints_v1.container_value_locals_v1` がある局所のみ値型縮退を許可する（Go focused regression 3 件追加）
8. [x] [ID: P2-SELFHOST-S8] Go emitter の runtime call 名解決を mapping.json に一本化する — emitter が mapping.json を迂回して `list_ctor` / `list.append` / `dict.get` / `set_ctor` / `sorted` などを個別 lower している箇所を mapping.json 経由へ寄せ、backend 内の runtime call 意味論の二重管理を解消する

### P3-COMMON-RENDERER-CPP: C++ emitter の CommonRenderer 移行 + fixture parity

文脈: [docs/ja/plans/p2-lowering-profile-common-renderer.md](../plans/p2-lowering-profile-common-renderer.md)
仕様: [docs/ja/spec/spec-language-profile.md](../spec/spec-language-profile.md) §8

1. [ ] [ID: P3-CR-CPP-S1] C++ emitter を CommonRenderer + override 構成に移行する — `src/toolchain2/emit/profiles/cpp.json` のプロファイルに従い、CommonRenderer の共通ノード走査を使う構成にする。C++ 固有のノード（ClassDef, FunctionDef, ForCore, With 等）だけ override として残す
2. [ ] [ID: P3-CR-CPP-S2] fixture 132 件 + sample 18 件の C++ compile + run parity を通す
3. [ ] [ID: P3-CR-CPP-S3] C++ runtime の dict_ops.h インクルードガード外コードを修正する — タプル用 `py_at` の実装が `#endif` の外に置かれており、多重インクルードで再定義エラーになる
4. [ ] [ID: P3-CR-CPP-S4] C++ runtime の py_types.h 例外安全性を修正する — `PyBoxedValue` と `ControlBlock` の2段階 `new` で最初の確保後に例外が起きるとメモリリーク。`make_unique` 等で対処する
5. [ ] [ID: P3-CR-CPP-S5] CommonRenderer の list/dict/tuple 出力で `source_span.lineno` を参照し、元ソースの改行を再現する — 現状の emitter は list リテラルを `", ".join(parts)` で1行に出力しており、元ソースの改行位置を無視している。前の要素と `source_span.lineno` が異なる場合に改行を入れる。synthetic module（type_id_table 等）は linker が適切な `source_span` を振ることで同じ仕組みで整形される

### P4-INT32: int のデフォルトサイズを int64 → int32 に変更

文脈: [docs/ja/plans/p4-int32-default.md](../plans/p4-int32-default.md)

前提: Go selfhost 完了後に着手。

1. [ ] [ID: P4-INT32-S1] spec-east.md / spec-east2.md の `int` → `int32` 正規化ルール変更
2. [ ] [ID: P4-INT32-S2] resolve の型正規化を修正
3. [ ] [ID: P4-INT32-S3] sample 18 件のオーバーフロー確認 + 必要な箇所を `int64` に明示
4. [ ] [ID: P4-INT32-S4] golden 再生成 + 全 emitter parity 確認

### P5-COMMON-RENDERER-GO: Go emitter の CommonRenderer 移行 + fixture parity

文脈: [docs/ja/plans/p2-lowering-profile-common-renderer.md](../plans/p2-lowering-profile-common-renderer.md)
仕様: [docs/ja/spec/spec-language-profile.md](../spec/spec-language-profile.md) §8

1. [ ] [ID: P5-CR-GO-S1] Go emitter を CommonRenderer + override 構成に移行する — `src/toolchain2/emit/profiles/go.json` のプロファイルに従い、CommonRenderer の共通ノード走査を使う構成にする。Go 固有のノード（FunctionDef のレシーバー、ForCore、multi_return 等）だけ override として残す
2. [ ] [ID: P5-CR-GO-S2] fixture 132 件 + sample 18 件の Go compile + run parity を通す

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

注: 完了済みタスクは [アーカイブ](archive/index.md) に移動済み。
