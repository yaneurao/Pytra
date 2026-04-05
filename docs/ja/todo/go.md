<a href="../../en/todo/go.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — Go backend

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-03-31 (P3-GO-LINT-FIX 完了)

## 運用ルール

- **旧 toolchain1（`src/toolchain/emit/go/`）は変更不可。** 新規開発・修正は全て `src/toolchain2/emit/go/` で行う（[spec-emitter-guide.md](../spec/spec-emitter-guide.md) §1）。
- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度順（小さい P 番号から）に着手する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモを追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。
- **parity テストは「emit + compile + run + stdout 一致」を完了条件とする。**
- **[emitter 実装ガイドライン](../spec/spec-emitter-guide.md)を必ず読むこと。** parity check ツール、禁止事項、mapping.json の使い方が書いてある。

## 未完了タスク

### P0-GO-NEW-FIXTURE-PARITY: 新規追加 fixture / stdlib の parity 確認

今セッション（2026-04-01〜05）で追加・更新した fixture と stdlib の parity を確認する。

対象: `bytes_copy_semantics`, `negative_index_comprehensive`, `negative_index_out_of_range`, `callable_optional_none`, `str_find_index`, `eo_extern_opaque_basic`(emit-only), `math_extended`(stdlib), `os_glob_extended`(stdlib)

1. [ ] [ID: P0-GO-NEWFIX-S1] 上記 fixture/stdlib の parity を確認する（対象 fixture のみ実行）

### P0-GO-TYPE-ID-CLEANUP: Go runtime から pytra_isinstance / py_runtime_object_type_id を削除する

仕様: [docs/ja/spec/spec-adt.md](../spec/spec-adt.md) §6

Go は `any` + type switch がネイティブにあるので `pytra_isinstance` / `py_runtime_object_type_id` は不要。emitter が type switch を直接生成するようにする。

1. [ ] [ID: P0-GO-TYPEID-CLN-S1] `src/runtime/go/built_in/py_runtime.go` から `pytra_isinstance` と `py_runtime_object_type_id` を削除する
2. [ ] [ID: P0-GO-TYPEID-CLN-S2] Go emitter の isinstance を `switch v := x.(type)` に置換する
3. [ ] [ID: P0-GO-TYPEID-CLN-S3] fixture + sample + stdlib parity に回帰がないことを確認する

### P7-GO-SELFHOST-RUNTIME: Go selfhost バイナリを実際に動かして parity PASS する

文脈: [docs/ja/plans/p7-go-selfhost-runtime.md](../plans/p7-go-selfhost-runtime.md)

P6 で go build は通ったが、selfhost バイナリが実際に fixture/sample/stdlib を変換して parity PASS するにはまだギャップがある。

1. [ ] [ID: P7-GO-SELFHOST-RT-S1] linker の type_id 割り当てで外部ベースクラス（CommonRenderer(ABC) 等）の階層解決を修正する — object にフォールバックする
2. [ ] [ID: P7-GO-SELFHOST-RT-S2] Go emitter 自身の Go 翻訳を selfhost golden に含める — 循環依存除外の見直し。`emit/go/` を golden に含められるようにする
3. [ ] [ID: P7-GO-SELFHOST-RT-S3] CLI wrapper（`main.go`）を追加する — EAST3 JSON を読んで Go コードを emit する最小エントリポイント
4. [ ] [ID: P7-GO-SELFHOST-RT-S4] `python3 tools/run/run_selfhost_parity.py --selfhost-lang go` を実行し、fixture + sample + stdlib の parity PASS を確認する
