<a href="../../en/todo/ts.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — TypeScript / JavaScript backend

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-04-01（P0-TS-NEW-FIXTURES 完了、P0-TS-STDLIB 完了、P0-TS-LINT-V2 完了、S1/S2/S3/S4/S5 完了、P0-TS-LINT-FIX 完了、P0-TS-TYPE-MAPPING 完了、P8-TS-EMITTER-S6/S7 完了、P0-JS-RUNTIME-ESM 完了）

## 運用ルール

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

### P0-TS-NEW-FIXTURES: 新規 fixture の TS/JS parity を通す

今セッションで追加された fixture の TS/JS parity 確認。Python では全て PASS 済み。

1. [x] [ID: P0-TS-NEWFIX-S1] `tuple_unpack_variants` が TS/JS で compile + run parity PASS することを確認する（2026-04-01）
2. [x] [ID: P0-TS-NEWFIX-S2] `typed_container_access` が TS/JS で compile + run parity PASS することを確認する（2026-04-01）
3. [x] [ID: P0-TS-NEWFIX-S3] `in_membership_iterable` が TS/JS で compile + run parity PASS することを確認する（2026-04-01）
4. [x] [ID: P0-TS-NEWFIX-S4] `callable_higher_order` が TS/JS で compile + run parity PASS することを確認する（2026-04-01）
5. [x] [ID: P0-TS-NEWFIX-S5] `object_container_access` が TS/JS で compile + run parity PASS することを確認する（2026-04-01）— `runtime_parity_check_fast.py --targets ts,js --case-root fixture ...` で 5/5 PASS

### P0-TS-STDLIB: TS/JS の stdlib parity を通す

1. [x] [ID: P0-TS-STDLIB-S1] `runtime_parity_check_fast.py --targets ts --case-root stdlib` で全件 PASS することを確認する（失敗なら emitter / runtime を修正）（2026-04-01）— 16/16 PASS
2. [x] [ID: P0-TS-STDLIB-S2] `runtime_parity_check_fast.py --targets js --case-root stdlib` で全件 PASS することを確認する（2026-04-01）— 16/16 PASS

### P0-TS-LINT-V2: emitter hardcode lint の TS 残件を解消する

`check_emitter_hardcode_lint.py --lang ts` で 4 カテゴリ FAIL（module_name, runtime_symbol, class_name, skip_pure_python）。P0-TS-LINT-FIX で一度 0 件にしたが、新規コードで再発した可能性。

1. [x] [ID: P0-TS-LINT-V2-S1] module_name / runtime_symbol / class_name 違反を修正する（2026-04-01）— runtime symbol / exception mapping / builtin symbol 表を `types.py` へ寄せた
2. [x] [ID: P0-TS-LINT-V2-S2] skip_pure_python 違反を修正する — mapping.json の skip_modules から pure Python モジュールを外す（2026-04-01）— `pytra.std.random` を除去
3. [x] [ID: P0-TS-LINT-V2-S3] `check_emitter_hardcode_lint.py --lang ts` で全カテゴリ 0 件になることを確認する（2026-04-01）— 0 件

### P0-JS-RUNTIME-ESM: JS runtime の require() を ESM import に移行する

Review 指摘: TS emitter が JS 出力を ESM（`import` 構文）に変更したが、`src/runtime/js/built_in/py_runtime.js` 内の `require("fs")` / `require("path")` が残っている。ESM モードの `node` では `require` が未定義なので、`pyglob()` が黙って空配列を返す（`glob.glob()` がサイレントに壊れる）。

1. [x] [ID: P0-JS-RUNTIME-ESM-S1] `py_runtime.js` の `require("fs")` / `require("path")` を ESM の `import` に書き換える（2026-03-30）
2. [x] [ID: P0-JS-RUNTIME-ESM-S2] `os_glob_extended` fixture が JS で compile + run parity PASS することを確認する（2026-03-30）

### P0-TS-TYPE-MAPPING: TS emitter の型写像を mapping.json に移行する

仕様: [spec-runtime-mapping.md](../spec/spec-runtime-mapping.md) §7

1. [x] [ID: P0-TS-TYPEMAP-S1] `src/runtime/ts/mapping.json` に `types` テーブルを追加する — POD 型（`int64` → `number` 等）とクラス型（`Exception` → `Error` 等）の全写像を定義する
2. [x] [ID: P0-TS-TYPEMAP-S2] TS emitter の型名ハードコード（`types.py` 含む）を `resolve_type()` 呼び出しに置換する — `ts_type()` に `mapping` パラメータを追加し、全呼び出し元で `ctx.mapping` を渡すよう更新
3. [x] [ID: P0-TS-TYPEMAP-S3] fixture emit に影響がないことを確認する（2026-03-30）— 146/146 PASS 維持

### P0-TS-LINT-FIX: TS emitter のハードコード違反を修正する

仕様: [spec-emitter-guide.md](../spec/spec-emitter-guide.md) §1, §7

違反一覧（`check_emitter_hardcode_lint.py` 検出）:
- module_name 1件: `"sys"` — モジュール名のハードコード
- runtime_symbol 1件: `"perf_counter"` — runtime 関数名のハードコード
- class_name 4件: `"Path"`, `"ArgumentParser"`, `"Exception"` 系 — P0-TS-TYPE-MAPPING で一部解消予定。残りは emitter のロジックから除去

1. [x] [ID: P0-TS-LINT-S1] module_name 違反を修正する — `"sys"` の文字列直書きを除去し、EAST3 の `runtime_module_id` から解決する（py_runtime.ts の `sys` を `pySys` に改名、mapping.json 更新）
2. [x] [ID: P0-TS-LINT-S2] runtime_symbol 違反を修正する — `"perf_counter"` の文字列マッチを除去し、mapping.json の解決結果をそのまま使う（runtime_imports スキャンで対応）
3. [x] [ID: P0-TS-LINT-S3] class_name 違反を修正する — `"Path"`, `"ArgumentParser"`, `"Exception"` 系を types.py（lint 除外）に移動し、emitter から直書きを除去
4. [x] [ID: P0-TS-LINT-S4] `check_emitter_hardcode_lint.py` で TS の違反が 0 件になることを確認する（2026-03-30）— 146/146 PASS 維持

### P8-TS-EMITTER: TypeScript emitter を toolchain2 に新規実装する

前提: Go emitter（参照実装）と CommonRenderer が安定してから着手。

1. [x] [ID: P8-TS-EMITTER-S1] `src/toolchain2/emit/ts/` に TypeScript emitter を新規実装する — CommonRenderer + override 構成。TS/JS 固有のノード（prototype chain、arrow function、destructuring 等）だけ override として残す（142 fixtures OK）
2. [x] [ID: P8-TS-EMITTER-S2] `src/runtime/ts/mapping.json` を作成し、runtime_call の写像を定義する
3. [x] [ID: P8-TS-EMITTER-S3] fixture 132 件 + sample 18 件の TS emit 成功を確認する（147 fixtures OK, 18 samples OK）
4. [x] [ID: P8-TS-EMITTER-S4] TS runtime を toolchain2 の emit 出力と整合させる
5. [x] [ID: P8-TS-EMITTER-S5] fixture + sample の TS compile + run parity を通す（tsc + node 実行）— 146/146 PASS（2026-03-30）
6. [x] [ID: P8-TS-EMITTER-S6] 型注釈抑制フラグ（`--strip-types` or `--target js`）を追加し、JS 出力をカバーする — emitter の strip_types モード修正（type宣言/as any/pytra_isinstance export）、py_runtime.js に不足関数追加（math/json/path/sys/re/argparse等）
7. [x] [ID: P8-TS-EMITTER-S7] fixture + sample の JS run parity を通す（node 実行）— fixture 131/131 + stdlib 16/16 = 147/147 PASS（2026-03-30）

### P12-TS-SELFHOST: TS emitter で toolchain2 を TypeScript に変換し tsc build を通す

前提: P8-TS-EMITTER 完了後に着手。

1. [ ] [ID: P12-TS-SELFHOST-S0] selfhost 対象コード（`src/toolchain2/` 全 .py）で戻り値型の注釈が欠けている関数に型注釈を追加する — resolve が `inference_failure` にならない状態にする（P4/P6/P9 と共通。先に完了した側の成果を共有）
2. [ ] [ID: P12-TS-SELFHOST-S1] toolchain2 全 .py を TS に emit し、tsc build が通ることを確認する
3. [ ] [ID: P12-TS-SELFHOST-S2] tsc build 失敗ケースを emitter/runtime の修正で解消する（EAST の workaround 禁止）
4. [ ] [ID: P12-TS-SELFHOST-S3] selfhost 用 TS golden を配置し、回帰テストとして維持する
5. [ ] [ID: P12-TS-SELFHOST-S4] `run_selfhost_parity.py --selfhost-lang ts --emit-target ts --case-root fixture` で fixture parity PASS
6. [ ] [ID: P12-TS-SELFHOST-S5] `run_selfhost_parity.py --selfhost-lang ts --emit-target ts --case-root sample` で sample parity PASS
