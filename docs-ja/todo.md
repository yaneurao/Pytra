# TODO（未完了）

> `docs-ja/` が正（source of truth）です。`docs/` はその翻訳です。

<a href="../docs/todo.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-02-24

## 文脈運用ルール

- 各タスクは `ID` と文脈ファイル（`docs-ja/plans/*.md`）を必須にする。
- 優先度上書きは `docs-ja/plans/instruction-template.md` 形式でチャット指示し、`todo2.md` は使わない。
- 着手対象は「未完了の最上位優先度ID（最小 `P<number>`、同一優先度では上から先頭）」に固定し、明示上書き指示がない限り低優先度へ進まない。
- `P0` が 1 件でも未完了なら `P1` 以下には着手しない。
- 着手前に文脈ファイルの `背景` / `非対象` / `受け入れ基準` を確認する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める（例: ``[ID: P0-XXX-01] ...``）。
- `docs-ja/todo.md` の進捗メモは 1 行要約に留め、詳細（判断・検証ログ）は文脈ファイル（`docs-ja/plans/*.md`）の `決定ログ` に記録する。
- 1 つの `ID` が大きい場合は、文脈ファイル側で `-S1` / `-S2` 形式の子タスクへ分割して進めてよい（親 `ID` 完了までは親チェックを維持）。
- 割り込み等で未コミット変更が残っている場合は、同一 `ID` を完了させるか差分を戻すまで別 `ID` に着手しない。
- `docs-ja/todo.md` / `docs-ja/plans/*.md` 更新時は `python3 tools/check_todo_priority.py` を実行し、差分に追加した進捗 `ID` が最上位未完了 `ID`（またはその子 `ID`）と一致することを確認する。
- 作業中の判断は文脈ファイルの `決定ログ` へ追記する。

## P0: EAST123 責務境界の可視化移行（最優先）

文脈: `docs-ja/plans/plan-east123-migration.md`（`TG-P0-EAST123-MIGRATION`）

## P1: CodeEmitter 共通ディスパッチ再設計

文脈: `docs-ja/plans/p1-codeemitter-dispatch-redesign.md`（`TG-P1-CED`）

## P1: コンパイラ共通層への抽出（py2cpp 偏在解消）

文脈: `docs-ja/plans/p1-compiler-shared-extraction.md`（`TG-P1-COMP-SHARED`）

1. [ ] [ID: P1-COMP-04] deps dump（`dump_deps_text`, `dump_deps_graph_text`）を共通 API 化し、CLI 層は表示/出力だけを担当する構成にする。
2. [ ] [ID: P1-COMP-05] 共通抽出後、`py2cpp.py` は C++ 固有責務（C++ runtime/header/multi-file 出力）へ限定する。
3. [ ] [ID: P1-COMP-09] `py2cpp.py` に残る汎用 helper（例: 文字列リスト整列、module 解析補助）を `src/pytra/compiler/` へ移管し、非 C++ 各 `py2*` から同一実装を再利用できる状態にする。
4. [ ] [ID: P1-COMP-10] 「全言語 selfhost を阻害しない共通層優先」の運用ルールを整備し、`py2cpp.py` へ汎用処理が再流入しない回帰チェック（lint/静的検査または CI ルール）を追加する。
5. [ ] [ID: P1-COMP-11] `src/pytra/compiler/transpile_cli.py` の汎用 helper 群を機能グループごとに `class + @staticmethod` へ整理し、`py2cpp.py` 側 import を class 単位へ縮退する。移行時はトップレベル互換ラッパーを暫定維持し、`tools/prepare_selfhost_source.py` / `test/unit/test_prepare_selfhost_source.py` の抽出ロジックも同時更新して selfhost 回帰を防ぐ。

進捗メモ:
- 詳細ログは `docs-ja/plans/p1-compiler-shared-extraction.md` の `決定ログ` を参照。

## P1: 多言語ランタイム配置統一

文脈: `docs-ja/plans/p1-runtime-layout-unification.md`（`TG-P1-RUNTIME-LAYOUT`）

目的: ランタイム配置を言語間で統一し、責務混在と重複実装を防ぐ。

1. [ ] [ID: P1-RUNTIME-01] Rust ランタイムを `src/rs_module/` から `src/runtime/rs/pytra/` へ段階移行し、`src/runtime/cpp/pytra/` と同等の責務分割（`built_in/`, `std/`, `utils/`, `compiler/`）に揃える。
2. [ ] [ID: P1-RUNTIME-01-S1] `src/rs_module/` の機能を責務別に棚卸しし、`src/runtime/rs/pytra/{built_in,std,utils,compiler}` への対応表を作る。
3. [ ] [ID: P1-RUNTIME-01-S2] Rust runtime ファイルを新配置へ段階移動し、互換 include/import レイヤを暫定維持する。
4. [ ] [ID: P1-RUNTIME-01-S3] selfhost/transpile 回帰を通したうえで `src/rs_module/` 依存を縮退する。
5. [ ] [ID: P1-RUNTIME-02] `py2rs.py` / Rust hooks のランタイム解決パスを `src/runtime/rs/pytra/` 基準へ更新する（`P1-RUNTIME-02-S1` から `P1-RUNTIME-02-S2` 完了でクローズ）。
6. [ ] [ID: P1-RUNTIME-02-S1] Rust emitter/hooks の path 解決箇所を特定し、新旧パス併用期間の互換仕様を定義する。
7. [ ] [ID: P1-RUNTIME-02-S2] 参照先を新パスへ切り替え、旧パス fallback を段階撤去する。
8. [ ] [ID: P1-RUNTIME-03] `src/rs_module/` の既存参照を洗い出し、互換レイヤを経由して最終的に廃止する（`P1-RUNTIME-03-S1` から `P1-RUNTIME-03-S2` 完了でクローズ）。
9. [ ] [ID: P1-RUNTIME-03-S1] `src/rs_module/` 参照元を全件列挙し、廃止可否を判定する。
10. [ ] [ID: P1-RUNTIME-03-S2] 参照を `src/runtime/rs/pytra/` 側へ置換し、`src/rs_module/` を削除する。
11. [ ] [ID: P1-RUNTIME-05] 各言語トランスパイラ（`py2cs.py`, `py2js.py`, `py2ts.py`, `py2go.py`, `py2java.py`, `py2kotlin.py`, `py2swift.py`）と hooks のランタイム解決パスを `src/runtime/<lang>/pytra/` 基準へ統一する（`P1-RUNTIME-05-S1` から `P1-RUNTIME-05-S3` 完了でクローズ）。
12. [ ] [ID: P1-RUNTIME-05-S1] 言語ごとの現行 runtime 解決パスを棚卸しし、差分一覧を作成する。
13. [ ] [ID: P1-RUNTIME-05-S2] 各 `py2<lang>.py` / hooks の参照先を `src/runtime/<lang>/pytra/` 基準へ順次更新する。
14. [ ] [ID: P1-RUNTIME-05-S3] 多言語 smoke で回帰確認し、旧パス互換レイヤを段階撤去する。

## P1: 多言語出力品質（`sample/cpp` 水準）

文脈: `docs-ja/plans/p1-multilang-output-quality.md`（`TG-P1-MULTILANG-QUALITY`）

1. [ ] [ID: P1-MQ-01] `sample/{rs,cs,js,ts,go,java,swift,kotlin}` の生成品質を計測し、`sample/cpp` 比での差分（過剰 `mut` / 括弧 / cast / clone / 未使用 import）を定量化する。
2. [ ] [ID: P1-MQ-02] 各言語 emitter/hooks/profile に段階的改善を入れ、`sample/cpp` と同等の可読性水準へ引き上げる。
3. [ ] [ID: P1-MQ-03] 多言語の出力品質回帰を防ぐ検査（品質指標 + transpile/smoke）を整備する。
4. [ ] [ID: P1-MQ-04] 非 C++ 各言語（`rs/cs/js/ts/go/java/swift/kotlin`）で、`py2<lang>.py` の selfhost 可否（自己変換した生成物で `sample/py` を再変換できるか）を検証し、言語別ステータスを記録する。
5. [ ] [ID: P1-MQ-05] 非 C++ 各言語で、生成物による再自己変換（多段 selfhost）が成立するかを検証し、失敗要因を分類する。
6. [ ] [ID: P1-MQ-06] 非 C++ 言語の selfhost / 多段 selfhost 検証を定期実行できるチェック導線（手順またはスクリプト）を整備する。
7. [ ] [ID: P1-MQ-07] `sample/` 生成物はタイムスタンプ埋め込みなしで管理し、CI で再生成差分ゼロ（常に最新）を必須化する。

## P3: microgpt 原本保全（低優先）

文脈: `docs-ja/plans/p3-microgpt-source-preservation.md`（`TG-P3-MICROGPT-SOURCE-PRESERVATION`）

1. [ ] [ID: P3-MSP-03] `work/tmp/microgpt-20260222-lite.py` 依存を縮退し、原本 `materials/refs/microgpt/microgpt-20260222.py` で transpile -> `g++ -fsyntax-only` が通る回帰導線を整備する。

進捗メモ:
- 詳細ログは `docs-ja/plans/p3-microgpt-source-preservation.md` の `決定ログ` を参照。

## P3: Pythonic 記法戻し（低優先）

文脈: `docs-ja/plans/p3-pythonic-restoration.md`（`TG-P3-PYTHONIC`）

### `src/py2cpp.py`

1. [ ] [ID: P3-PY-01] `while i < len(xs)` + 手動インデックス更新を `for x in xs` / `for i, x in enumerate(xs)` へ戻す。
2. [ ] [ID: P3-PY-03] 空 dict/list 初期化後の逐次代入（`out = {}; out["k"] = v`）を、型崩れしない箇所から辞書リテラルへ戻す。
3. [ ] [ID: P3-PY-04] 三項演算子を回避している箇所（`if ...: a=x else: a=y`）を、selfhost 側対応後に式形式へ戻す。
4. [ ] [ID: P3-PY-05] import 解析の一時変数展開（`obj = ...; s = any_to_str(obj)`）を、型安全が確保できる箇所から簡潔化する。

進捗メモ:
- 詳細ログは `docs-ja/plans/p3-pythonic-restoration.md` の `決定ログ` を参照。

### 作業ルール

1. [ ] [ID: P3-RULE-01] 1パッチで戻す範囲は 1〜3 関数に保つ。
2. [ ] [ID: P3-RULE-02] 各パッチで `python3 tools/check_py2cpp_transpile.py` を実行する。
3. [ ] [ID: P3-RULE-03] 各パッチで `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented` を実行する。
4. [ ] [ID: P3-RULE-04] 回帰が出た場合は「可読性改善より selfhost 安定」を優先する。

## P3: サンプル実行時間の再計測とREADME更新（低優先）

文脈: `docs-ja/plans/p3-sample-benchmark-refresh.md`（`TG-P3-SAMPLE-BENCHMARK`）

1. [ ] [ID: P3-SB-01] サンプルコード変更（実行時間変化）、サンプル番号再編（04/15/17/18）、サンプル数増加（01〜18）を反映するため、全ターゲット言語（Python/C++/Rust/C#/JS/TS/Go/Java/Swift/Kotlin）で実行時間を再計測し、トップページの `readme.md` / `readme-ja.md` の比較表を同一データで更新する。

## メモ

- このファイルは未完了タスクのみを保持します。
- 完了済みタスクは `docs-ja/todo-history/index.md` 経由で履歴へ移動します。
- `docs-ja/todo-history/index.md` は索引のみを保持し、履歴本文は `docs-ja/todo-history/YYYYMMDD.md` に日付単位で保存します。
