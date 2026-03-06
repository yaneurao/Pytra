# TODO（未完了）

> `docs/ja/` が正（source of truth）です。`docs/en/` はその翻訳です。

<a href="../../en/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-03-06

## 文脈運用ルール

- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度上書きは `docs/ja/plans/instruction-template.md` 形式でチャット指示し、`todo2.md` は使わない。
- 着手対象は「未完了の最上位優先度ID（最小 `P<number>`、同一優先度では上から先頭）」に固定し、明示上書き指示がない限り低優先度へ進まない。
- `P0` が 1 件でも未完了なら `P1` 以下には着手しない。
- 着手前に文脈ファイルの `背景` / `非対象` / `受け入れ基準` を確認する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める（例: ``[ID: P0-XXX-01] ...``）。
- `docs/ja/todo/index.md` の進捗メモは 1 行要約に留め、詳細（判断・検証ログ）は文脈ファイル（`docs/ja/plans/*.md`）の `決定ログ` に記録する。
- 1 つの `ID` が大きい場合は、文脈ファイル側で `-S1` / `-S2` 形式の子タスクへ分割して進めてよい（親 `ID` 完了までは親チェックを維持）。
- 割り込み等で未コミット変更が残っている場合は、同一 `ID` を完了させるか差分を戻すまで別 `ID` に着手しない。
- `docs/ja/todo/index.md` / `docs/ja/plans/*.md` 更新時は `python3 tools/check_todo_priority.py` を実行し、差分に追加した進捗 `ID` が最上位未完了 `ID`（またはその子 `ID`）と一致することを確認する。
- 作業中の判断は文脈ファイルの `決定ログ` へ追記する。
- 一時出力は既存 `out/`（または必要時のみ `/tmp`）を使い、リポジトリ直下に新規一時フォルダを増やさない。

## メモ

- このファイルは未完了タスクのみを保持します。
- 完了済みタスクは `docs/ja/todo/archive/index.md` 経由で履歴へ移動します。
- `docs/ja/todo/archive/index.md` は索引のみを保持し、履歴本文は `docs/ja/todo/archive/YYYYMMDD.md` に日付単位で保存します。


## 未完了タスク

### P0: C++ unit 回帰の根本修復（SoT/IR/Emitter/Runtime 契約の整流）

文脈: [docs/ja/plans/p0-cpp-unit-regression-recovery.md](../plans/p0-cpp-unit-regression-recovery.md)

1. [ ] [ID: P0-CPP-REGRESSION-RECOVERY-01] C++ unit 回帰を、SoT/IR/Emitter/Runtime 契約の順で根本修復し、unit + fixture/sample parity を再緑化する。
2. [x] [ID: P0-CPP-REGRESSION-RECOVERY-01-S1-01] failing test を「generated runtime」「import/include 解決」「container 意味論」「emitter/CLI 契約」に再分類し、修正責務の所属レイヤを固定する。
3. [x] [ID: P0-CPP-REGRESSION-RECOVERY-01-S2-01] `json` generated runtime の破綻を、SoT と C++ runtime 生成契約の修正で解消する（`.gen.*` 手修正禁止）。
4. [x] [ID: P0-CPP-REGRESSION-RECOVERY-01-S2-02] `argparse` generated runtime の破綻を、SoT・reserved name 回避・class/member emission 契約の修正で解消する。
5. [ ] [ID: P0-CPP-REGRESSION-RECOVERY-01-S3-01] `pytra.utils.{png,gif}` と `pytra.std.{time,pathlib}` の import 解決・include dedupe/sort・one-to-one module include 契約を修正する。
6. [ ] [ID: P0-CPP-REGRESSION-RECOVERY-01-S3-02] `os.path` / `glob` 系 runtime helper 呼び出しを、owner/module metadata に基づく解決へ戻し、C++ emitter の特例依存を減らす。
7. [ ] [ID: P0-CPP-REGRESSION-RECOVERY-01-S4-01] `dict.items()` / `dict.get()` / `any()` / dict/set comprehension の container-view・iterator 意味論を、built_in SoT と runtime adapter の整合で修正する。
8. [ ] [ID: P0-CPP-REGRESSION-RECOVERY-01-S4-02] `mod_mode`、stmt dispatch fallback、CLI `dump-options` / error category の C++ emitter 契約を整理し、option 反映と診断整合を修正する。
9. [ ] [ID: P0-CPP-REGRESSION-RECOVERY-01-S5-01] C++ unit 全体、fixture parity、sample parity を再実行し、回帰が残らないことを確認して docs/ja/todo を更新する。

- 進捗メモ: 2026-03-06 [ID: `P0-CPP-REGRESSION-RECOVERY-01-S1-01`] `test/unit/backends/cpp` の fail を代表ケース単体再実行で再分類し、`json/argparse` は generated runtime 契約、`png/gif/time/pathlib` は public include 契約、`os.path/glob` は owner/module metadata 解決、`dict.items/get/any/comprehension` は container adapter、`mod_mode/emit_stmt/CLI` は emitter/CLI 契約の破綻として固定した。
- 進捗メモ: 2026-03-06 [ID: `P0-CPP-REGRESSION-RECOVERY-01-S2-01`] `json` について class split の brace 誤判定、`\\b/\\f` 未escape、runtime header の既定引数欠落、runtime `.cpp` 定義側の既定引数剥離不足を修正し、`src/pytra/std/json.py` から `json.gen.*` を再生成した。`test_json_extended_runtime` は compile/run まで通過。
- 進捗メモ: 2026-03-06 [ID: `P0-CPP-REGRESSION-RECOVERY-01-S2-02`] `argparse` について imported runtime class method の keyword 引数を default 補完込みで C++ positional call へ整列するよう emitter を拡張し、`src/pytra/std/argparse.py` も optional/value-class dict 依存を減らす形へ整理した。`argparse.gen.*` を再生成し、`test_argparse_extended_runtime` は compile/run まで通過。
