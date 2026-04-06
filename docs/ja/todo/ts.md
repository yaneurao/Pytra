<a href="../../en/todo/ts.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — TypeScript / JavaScript backend

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-04-06

## 運用ルール

- **旧 toolchain1（`src/toolchain/emit/ts/`）は変更不可。** 新規開発・修正は全て `src/toolchain2/emit/ts/` で行う（[spec-emitter-guide.md](../spec/spec-emitter-guide.md) §1）。
- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度順（小さい P 番号から）に着手する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモを追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。
- **parity テストは「emit + compile + run + stdout 一致」を完了条件とする。**
- **[emitter 実装ガイドライン](../spec/spec-emitter-guide.md)を必ず読むこと。** parity check ツール、禁止事項、mapping.json の使い方が書いてある。

## 現状

- toolchain2 に TS/JS emitter は未実装（`src/toolchain2/emit/ts/`, `src/toolchain2/emit/js/` が存在しない）
- runtime は `src/runtime/ts/`, `src/runtime/js/` に存在する（旧 toolchain1 時代の実装）
- 旧 toolchain1 の TS/JS emitter は `src/toolchain/emit/ts/`, `src/toolchain/emit/js/` に存在するが、toolchain2 への移行が必要

## 設計方針

TypeScript emitter を先に実装し、JavaScript は型注釈の出力を抑制するフラグで対応する。

- EAST3 には完全な型情報がある。TS emitter はこれを素直に型注釈付きで出力する
- JS モードは同じ emitter で型注釈を省略するだけ（`--strip-types` または `--target js`）
- emitter を2本作る必要はない。TS emitter 1本 + フラグで JS/TS の両方をカバーする

## 未完了タスク

### P0-TS-SHIM-CLEANUP: TS/JS runtime の Python ビルトイン shim を廃止する

文脈: [docs/ja/plans/plan-ts-runtime-shim-cleanup.md](../plans/plan-ts-runtime-shim-cleanup.md)

`py_runtime.ts` / `py_runtime.js` が `export const int = Number` / `export function match(...)` のように Python ビルトイン名を shim として export している。emitter が EAST3 の `runtime_call` / `mapping.json` を使って TS/JS 固有の名前に解決すべき。TS と JS の両方が対象。

1. [x] [ID: P0-TS-SHIM-S1] `py_runtime.ts` / `py_runtime.js` から export されている Python ビルトイン名の shim を調査・一覧化する（2026-04-02）— `int=Number`, `float=Number`, `bool=Boolean`, `str=String`, `match`/`sub`/`search`/`findall`/`split`(re関数), `perf_counter`, `sys`, `dict()`/`list()`/`set_()` が対象。型alias(`type int = number`等)は維持、値exportをmapping.json解決に移行する
2. [x] [ID: P0-TS-SHIM-S2] TS/JS emitter が mapping.json の `calls` テーブルで解決するよう修正し、shim export を削除する（2026-04-06）— 旧 `src/toolchain/emit/ts/` の current parity backend で、Python builtin shim (`int` / `float` / `bool` / `str` / `perf_counter`) 依存を除去。attr-call も owner type + `mapping.json` marker 展開へ寄せ、`with` / ctor / runtime import の stale 経路も metadata ベースへ整理
3. [x] [ID: P0-TS-SHIM-S3] fixture + sample + stdlib の TS parity および JS parity に回帰がないことを確認する（2026-04-06）— sample `18/18 PASS`、selected fixture `from_import_symbols` / `with_statement` / `with_context_manager` / `sorted_basic` / `float_constructor`、selected stdlib `pytra_runtime_png` / `pathlib_extended` で TS/JS PASS。`check_emitter_hardcode_lint.py --lang ts` と `check_runtime_call_coverage.py --lang ts --direction mapping-to-east` も PASS

### P12-TS-SELFHOST: TS emitter で toolchain2 を TypeScript に変換し tsc build を通す

前提: P8-TS-EMITTER 完了後に着手。

1. [ ] [ID: P12-TS-SELFHOST-S0] selfhost 対象コード（`src/toolchain2/` 全 .py）で戻り値型の注釈が欠けている関数に型注釈を追加する — resolve が `inference_failure` にならない状態にする（P4/P6/P9 と共通。先に完了した側の成果を共有）
2. [ ] [ID: P12-TS-SELFHOST-S1] toolchain2 全 .py を TS に emit し、tsc build が通ることを確認する
3. [ ] [ID: P12-TS-SELFHOST-S2] tsc build 失敗ケースを emitter/runtime の修正で解消する（EAST の workaround 禁止）
4. [ ] [ID: P12-TS-SELFHOST-S3] selfhost 用 TS golden を配置し、回帰テストとして維持する
5. [ ] [ID: P12-TS-SELFHOST-S4] `run_selfhost_parity.py --selfhost-lang ts --emit-target ts --case-root fixture` で fixture parity PASS
6. [ ] [ID: P12-TS-SELFHOST-S5] `run_selfhost_parity.py --selfhost-lang ts --emit-target ts --case-root sample` で sample parity PASS
