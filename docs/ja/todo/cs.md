<a href="../../en/todo/cs.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — C# backend

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

## 参考資料

- 旧 toolchain1 の C# emitter: `src/toolchain/emit/cs/`
- toolchain2 の TS emitter（参考実装）: `src/toolchain2/emit/ts/`
- 既存の C# runtime: `src/runtime/cs/`
- emitter 実装ガイドライン: `docs/ja/spec/spec-emitter-guide.md`
- mapping.json 仕様: `docs/ja/spec/spec-runtime-mapping.md`

## 未完了タスク

### P0-CS-TYPE-ID-CLEANUP: C# runtime から PYTRA_TID_* / pytra_isinstance を削除する

仕様: [docs/ja/spec/spec-adt.md](../spec/spec-adt.md) §6

C# は `is` / `switch` がネイティブにあるので `PYTRA_TID_*` 定数 (26個)、`pytra_isinstance`、`type_id_table` は不要。

1. [x] [ID: P0-CS-TYPEID-CLN-S1] `src/runtime/cs/built_in/py_runtime.cs` から `PYTRA_TID_*` 定数と `pytra_isinstance` を削除する
   完了メモ: neutral internal type constants へ置換し、`pytra_isinstance` を削除。`py_is_set` と Python 風 container/tuple repr を runtime に追加して C# parity を維持。
2. [x] [ID: P0-CS-TYPEID-CLN-S2] `src/runtime/cs/generated/built_in/type_id.cs` を削除する
   完了メモ: 生成済み `type_id.cs` を削除。`check_emitter_hardcode_lint.py --lang cs --include-runtime` は 0 件。
3. [x] [ID: P0-CS-TYPEID-CLN-S3] C# emitter の isinstance を `x is Type t` に置換する
   完了メモ: toolchain2 C# emitter で builtin/user class/container の `isinstance` を native `is` 判定へ移行。legacy `PYTRA_TID_*` expected type も型名へ正規化。
4. [ ] [ID: P0-CS-TYPEID-CLN-S4] fixture + sample + stdlib parity に回帰がないことを確認する
   進捗メモ: `stdlib 16/16 PASS`。fixture は個別 blocker（`none_optional`, `typed_container_access`, `str_repr_containers`）を解消済みだが full rerun 未再実施。sample は run_failed を解消し、残りは artifact CRC mismatch 7 件（`01_mandelbrot`, `02_raytrace_spheres`, `03_julia_set`, `04_orbit_trap_julia`, `06_julia_parameter_sweep`, `14_raymarching_light_cycle`, `16_glass_sculpture_chaos`）。

### P3-CS-SELFHOST: C# emitter で toolchain2 を C# に変換し build を通す

文脈: [docs/ja/plans/p3-cs-selfhost.md](../plans/p3-cs-selfhost.md)

1. [ ] [ID: P3-CS-SELFHOST-S0] selfhost 対象コード（`src/toolchain2/` 全 .py）で戻り値型の注釈が欠けている関数に型注釈を追加する — resolve が `inference_failure` にならない状態にする（他言語と共通。先に完了した側の成果を共有）
2. [ ] [ID: P3-CS-SELFHOST-S1] toolchain2 全 .py を C# に emit し、build が通ることを確認する
3. [ ] [ID: P3-CS-SELFHOST-S2] build 失敗ケースを emitter/runtime の修正で解消する（EAST の workaround 禁止）
4. [ ] [ID: P3-CS-SELFHOST-S3] selfhost 用 C# golden を配置し、回帰テストとして維持する
5. [ ] [ID: P3-CS-SELFHOST-S4] `run_selfhost_parity.py --selfhost-lang cs --emit-target cs --case-root fixture` で fixture parity PASS
6. [ ] [ID: P3-CS-SELFHOST-S5] `run_selfhost_parity.py --selfhost-lang cs --emit-target cs --case-root sample` で sample parity PASS
