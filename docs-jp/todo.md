# TODO（未完了）

> `docs-jp/` が正（source of truth）です。`docs/` はその翻訳です。

<a href="../docs/todo.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-02-23

## 文脈運用ルール

- 各タスクは `ID` と文脈ファイル（`docs-jp/plans/*.md`）を必須にする。
- 優先度上書きは `docs-jp/plans/instruction-template.md` 形式でチャット指示し、`todo2.md` は使わない。
- 着手対象は「未完了の最上位優先度ID（最小 `P<number>`、同一優先度では上から先頭）」に固定し、明示上書き指示がない限り低優先度へ進まない。
- `P0` が 1 件でも未完了なら `P1` 以下には着手しない。
- 着手前に文脈ファイルの `背景` / `非対象` / `受け入れ基準` を確認する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める（例: ``[ID: P0-XXX-01] ...``）。
- `docs-jp/todo.md` の進捗メモは 1 行要約に留め、詳細（判断・検証ログ）は文脈ファイル（`docs-jp/plans/*.md`）の `決定ログ` に記録する。
- 1 つの `ID` が大きい場合は、文脈ファイル側で `-S1` / `-S2` 形式の子タスクへ分割して進めてよい（親 `ID` 完了までは親チェックを維持）。
- 割り込み等で未コミット変更が残っている場合は、同一 `ID` を完了させるか差分を戻すまで別 `ID` に着手しない。
- `docs-jp/todo.md` / `docs-jp/plans/*.md` 更新時は `python3 tools/check_todo_priority.py` を実行し、差分に追加した進捗 `ID` が最上位未完了 `ID`（またはその子 `ID`）と一致することを確認する。
- 作業中の判断は文脈ファイルの `決定ログ` へ追記する。

## P0: Runtime 起源分離（最優先）

文脈: `docs-jp/plans/p1-runtime-layout-unification.md`（`TG-P1-RUNTIME-LAYOUT`）

1. [x] [ID: P0-RUNTIME-SEP-01] C++ runtime を「生成物」と「手書き」で上位フォルダ分離する（`P0-RUNTIME-SEP-01-S1` から `P0-RUNTIME-SEP-01-S5` 完了でクローズ）。
2. [x] [ID: P0-RUNTIME-SEP-01-S1] `src/runtime/cpp/pytra/` 配下の現状を棚卸しし、`std/`・`built_in/`・`utils/`・`compiler/` の各ファイルを「生成物 / 手書き / 入口フォワーダー」に分類する。
3. [x] [ID: P0-RUNTIME-SEP-01-S2] `src/runtime/cpp/pytra-gen/`（自動生成専用）と `src/runtime/cpp/pytra-core/`（手書き専用）を新設し、ビルド/インクルード解決を破壊しない最小構成を作る。
4. [x] [ID: P0-RUNTIME-SEP-01-S3] 自動生成ファイルを `pytra-gen` へ段階移動し、`AUTO-GENERATED` ヘッダ付与を統一する。
5. [x] [ID: P0-RUNTIME-SEP-01-S4] 手書きファイル（`-impl` 含む）を `pytra-core` へ段階移動し、`src/runtime/cpp/pytra/` を公開 include 入口（薄いフォワーダー）へ縮退する。
6. [x] [ID: P0-RUNTIME-SEP-01-S5] CI ガードを追加し、`pytra-gen` は `AUTO-GENERATED` 必須、`pytra-core` は `AUTO-GENERATED` 禁止を強制する。

方針メモ:
- ターゲット言語の増加を前提に、runtime は「自動生成層を厚く・手書き層を薄く」を基本方針とする。意味論は可能な限り `src/pytra/` 側の正本から生成し、手書きは GC/ABI など低レベル最小層へ限定する。

進捗メモ:
- `P0-RUNTIME-SEP-01-S1`: `docs-jp/plans/p1-runtime-layout-unification-inventory.md` に `src/runtime/cpp/pytra/` 全57ファイルの分類台帳（`generated=38`, `handwritten=19`, `entry_forwarder=0`）を追加した。
- `P0-RUNTIME-SEP-01-S2`: `src/runtime/cpp/pytra-gen/` と `src/runtime/cpp/pytra-core/` を新設し、各ディレクトリに責務境界と禁止事項（生成物必須/禁止）を明記した。
- `P0-RUNTIME-SEP-01-S3`: 生成物38ファイル（`std/*`, `utils/*`, `compiler/east_parts/core.*`）を `src/runtime/cpp/pytra-gen/` へ移動し、旧 `src/runtime/cpp/pytra/` には互換フォワーダー（`.h/.cpp`）を配置した。`src/py2cpp.py --emit-runtime-cpp` の出力先も `pytra-gen` へ変更した。
- `P0-RUNTIME-SEP-01-S4`: 手書き19ファイル（`built_in/*`, `std/*-impl.*`）を `src/runtime/cpp/pytra-core/` へ移動し、`src/runtime/cpp/pytra/` の全57ファイルをフォワーダー化した（公開入口として維持）。
- `P0-RUNTIME-SEP-01-S5`: `tools/check_runtime_cpp_layout.py` を追加し、`tools/run_local_ci.py` へ組み込んで `pytra-gen` の `AUTO-GENERATED` 必須と `pytra-core` の同マーカー禁止を CI で強制した。

## P0: type_id 継承判定・isinstance 統一（最優先）

文脈: `docs-jp/plans/p0-typeid-isinstance-dispatch.md`（`TG-P0-TYPEID-ISINSTANCE`）

1. [x] [ID: P0-TID-01] `type_id` ベースの共通判定 API（`py_isinstance` / `py_is_subtype`）を C++/JS/TS runtime と各 emitter lower に統一導入する（`P0-TID-01-S1` から `P0-TID-01-S4` 完了でクローズ）。
2. [x] [ID: P0-TID-01-S1] `docs-jp/spec/spec-type_id.md` / `docs-jp/spec/spec-boxing.md` / `docs-jp/spec/spec-iterable.md` の整合を取り、`isinstance` 判定の共通 API 契約を確定する。
3. [x] [ID: P0-TID-01-S2] C++ runtime に `py_isinstance` / `py_is_subtype` を実装し、既存 call site を段階的に置換する。
4. [x] [ID: P0-TID-01-S3] JS/TS runtime に同等 API を実装し、`type_id` dispatch のオン/オフ方針（オプション切替）と整合させる。
5. [x] [ID: P0-TID-01-S4] `py2cpp` を含む各 emitter の `isinstance` lower を runtime API 経由へ統一し、target 固有 built-in 直書き分岐を縮退する。
6. [ ] [ID: P0-TID-02] `src/pytra/built_in/`（pure Python）を runtime 意味論の正本として新設し、target 非依存 built-in 処理を段階移管する（`P0-TID-02-S1` から `P0-TID-02-S4` 完了でクローズ）。
7. [ ] [ID: P0-TID-02-S1] `src/pytra/built_in/` の配置・命名・生成対象ルールを定義し、最小スケルトンを作成する。
8. [ ] [ID: P0-TID-02-S2] `isinstance` / `issubclass` / `type_id` の pure Python 実装を `src/pytra/built_in/` へ移管する。
9. [ ] [ID: P0-TID-02-S3] `py2cpp.py --emit-runtime-cpp` を拡張し、`src/pytra/built_in/*.py` から `src/runtime/cpp/pytra/built_in/*.{h,cpp}` を生成できるようにする。
10. [ ] [ID: P0-TID-02-S4] C++ 側の手書き built-in 実装を最小ブート層（GC/ABI 等）へ限定し、移管済み処理の重複実装を解消する。

進捗メモ:
- `P0-TID-01-S1`: `spec-type_id` / `spec-boxing` / `spec-iterable` の3文書で、`--object-dispatch-mode` の一括切替範囲と `py_is_subtype` / `py_isinstance` / `py_issubclass` 契約を揃えて明文化した。
- `P0-TID-01-S2`: C++ runtime（`py_runtime.h`）に `py_is_subtype` / `py_issubclass` / `py_isinstance` を実装し、`py2cpp` の `isinstance` lower が `py_isinstance(..., <type_id>)` を生成する回帰を `test/unit/test_py2cpp_codegen_issues.py` で確認した。
- `P0-TID-01-S3`: JS/TS runtime に `pyIsSubtype` / `pyIsInstance` と `pyRegisterClassType` ベースの型ID運用を実装し、`test/unit/test_js_ts_runtime_dispatch.py` / `test/unit/test_py2js_smoke.py` / `test/unit/test_py2ts_smoke.py` で回帰を確認した。
- `P0-TID-01-S4`: emitter 側の `isinstance` lower を runtime API 経由へ統一し、C++/JS/TS/C#/Rust の回帰を `test/unit/test_py2cs_smoke.py` / `test/unit/test_py2rs_smoke.py` と `tools/check_py2{cpp,js,ts,cs,rs}_transpile.py` で確認した。
- 詳細ログは `docs-jp/plans/p0-typeid-isinstance-dispatch.md` の `決定ログ` を参照。

## P0: Iterable/Iterator 契約反映（最優先）

文脈: `docs-jp/plans/p0-iterable-runtime-protocol.md`（`TG-P0-ITER`）

1. [ ] [ID: P0-ITER-01] `docs-jp/spec/spec-iterable.md` を正本として iterable/iterator 契約を実装全体へ反映する（`P0-ITER-01-S1` から `P0-ITER-01-S4` 完了でクローズ）。
2. [ ] [ID: P0-ITER-01-S1] `EAST` trait（`iterable_trait` / `iter_mode`）の必要情報と既存ノード影響を整理し、導入手順を確定する。
3. [ ] [ID: P0-ITER-01-S2] `EAST` trait を導入し、parser/lower から必要メタデータを供給できる状態にする。
4. [ ] [ID: P0-ITER-01-S3] C++ runtime（`py_iter_or_raise` / `py_next_or_stop` / `py_dyn_range`）を実装し、`spec-iterable` の契約を満たす。
5. [ ] [ID: P0-ITER-01-S4] `py2cpp` codegen の `static_fastpath` / `runtime_protocol` 分岐を実装し、回帰テストを追加する。

進捗メモ:
- 詳細ログは `docs-jp/plans/p0-iterable-runtime-protocol.md` の `決定ログ` を参照。

## P0: Selfhost 安定化

文脈: `docs-jp/plans/p0-selfhost-stabilization.md`（`TG-P0-SH`）

1. [ ] [ID: P0-SH-04] `tools/prepare_selfhost_source.py` に残る selfhost 専用スタブ整理を完了する（`P0-SH-04-S1` から `P0-SH-04-S3` 完了でクローズ）。
2. [ ] [ID: P0-SH-04-S1] 残存スタブを棚卸しし、「恒久機能化すべきもの」と「削除すべきもの」を分類する。
3. [ ] [ID: P0-SH-04-S2] 恒久機能化対象を compiler/runtime 側へ移し、prepare 側分岐を段階削減する。
4. [ ] [ID: P0-SH-04-S3] selfhost 回帰（通常 + guard profile）を再計測し、prepare スクリプト依存の再流入を防ぐ。
5. [x] [ID: P0-SH-05] selfhost 暴走対策として fail-fast ガードを導入し、`--guard-profile {off,default,strict}` と個別上限（`--max-ast-depth`, `--max-parse-nodes`, `--max-symbols-per-module`, `--max-scope-depth`, `--max-import-graph-nodes`, `--max-import-graph-edges`, `--max-generated-lines`）を CLI から指定可能にする。制限超過時は `input_invalid(kind=limit_exceeded, stage=...)` で早期停止する。

進捗メモ:
- 詳細ログは `docs-jp/plans/p0-selfhost-stabilization.md` の `決定ログ` を参照。

## P1: CodeEmitter / Hooks 移行

文脈: `docs-jp/plans/p1-codeemitter-hooks-migration.md`（`TG-P1-CEH`）

1. [ ] [ID: P1-CEH-01] profile で表現しづらいケースだけを hooks へ移し、`py2cpp.py` 側条件分岐を残さない状態にする（`P1-CEH-01-S1` から `P1-CEH-01-S4` 完了でクローズ）。
2. [ ] [ID: P1-CEH-01-S1] `py2cpp.py` 側の profile/hook 境界違反ケースを棚卸しし、移行優先順位を決める。
3. [ ] [ID: P1-CEH-01-S2] hook 化しやすいケースから `CodeEmitter` hooks へ移行し、`py2cpp.py` 条件分岐を削減する。
4. [ ] [ID: P1-CEH-01-S3] hook 化が難しいケースは profile 側表現力拡張で吸収し、target 固有分岐の再追加を防ぐ。
5. [ ] [ID: P1-CEH-01-S4] selfhost/fixture 回帰で生成差分を確認し、残る `py2cpp.py` 分岐を除去する。

## P1: CodeEmitter 共通ディスパッチ再設計

文脈: `docs-jp/plans/p1-codeemitter-dispatch-redesign.md`（`TG-P1-CED`）

1. [ ] [ID: P1-CED-01] `render_expr` の kind ごとに hook ポイントを追加する。
2. [ ] [ID: P1-CED-02] `emit_stmt` も kind ごとの hook ポイントへ分解する。
3. [ ] [ID: P1-CED-03] `CppEmitter` を hook 優先 + fallback の二段構成に統一する。
4. [ ] [ID: P1-CED-04] `tools/check_selfhost_cpp_diff.py` で差分ゼロを維持しながら fallback を縮退する。
5. [ ] [ID: P1-CED-05] fallback が十分に減った段階で、共通ディスパッチを `CodeEmitter` 本体へ戻す。

受け入れ基準:
1. [ ] [ID: P1-CED-AC-01] Python 実行パス: `hooks` 有効時に既存ケースのコード生成結果が不変。
2. [ ] [ID: P1-CED-AC-02] selfhost 実行パス: `mismatches=0` を維持。
3. [ ] [ID: P1-CED-AC-03] `py2cpp.py` の `render_expr` / `emit_stmt` 本体分岐が段階的に短くなる。

py2cpp / py2rs 共通化候補:
1. [ ] [ID: P1-CED-A-01] 優先 A: `If` / `While` / `ForRange` / `For` の文スケルトン生成（開閉ブロック + scope push/pop）を `CodeEmitter` へ移す。
2. [ ] [ID: P1-CED-A-02] 優先 A: `Assign` / `AnnAssign` / `AugAssign` の「宣言判定 + 代入先レンダ」共通骨格を `CodeEmitter` へ移す。
3. [ ] [ID: P1-CED-A-03] 優先 A: `Compare` / `BoolOp` / `IfExp` の式組み立てを `CodeEmitter` へ移す。
4. [ ] [ID: P1-CED-A-04] 優先 A: import 束縛テーブル読み込み（`meta.import_bindings` 反映）を `CodeEmitter` へ移す。
5. [ ] [ID: P1-CED-B-01] 優先 B: 型名正規化 + 言語型への最終写像（`normalize_type_name` 後段）を共通化する。
6. [ ] [ID: P1-CED-B-02] 優先 B: `Call` 前処理（`_prepare_call_parts` 結果の共通利用）を共通化する。
7. [ ] [ID: P1-CED-B-03] 優先 B: `Tuple` 代入の一時変数 lower を共通化する。
8. [ ] [ID: P1-CED-C-01] 優先 C: 言語別ランタイム関数へのルーティング（profile + hooks）を共通化する。
9. [ ] [ID: P1-CED-C-02] 優先 C: 文字列/配列の細かい最適化（演算子簡約・括弧削減）を共通化する。

## P1: py2cpp 縮退（行数削減）

文脈: `docs-jp/plans/p1-py2cpp-reduction.md`（`TG-P1-CPP-REDUCE`）

1. [ ] [ID: P1-CPP-REDUCE-01] `src/py2cpp.py` に残る未移行ロジックを `CodeEmitter` へ段階移管し、行数を縮退する（`P1-CPP-REDUCE-01-S1` から `P1-CPP-REDUCE-01-S3` 完了でクローズ）。
2. [ ] [ID: P1-CPP-REDUCE-01-S1] `py2cpp.py` 内ロジックを「言語非依存」「C++固有」に分類し、移管順を確定する。
3. [ ] [ID: P1-CPP-REDUCE-01-S2] 言語非依存ロジックを `CodeEmitter` / `src/pytra/compiler/` へ段階移管する。
4. [ ] [ID: P1-CPP-REDUCE-01-S3] selfhost 差分ゼロを維持したまま `py2cpp.py` の重複分岐を削減する。
5. [ ] [ID: P1-CPP-REDUCE-02] 全言語 selfhost 前提で `py2cpp.py` への汎用 helper 新規追加を原則禁止する運用へ移行する（`P1-CPP-REDUCE-02-S1` から `P1-CPP-REDUCE-02-S3` 完了でクローズ）。
6. [ ] [ID: P1-CPP-REDUCE-02-S1] 「汎用 helper 禁止 / 共通層先行抽出」の運用ルールを文書化する。
7. [ ] [ID: P1-CPP-REDUCE-02-S2] 既存 helper 追加箇所を検出する lint/CI チェックを追加する。
8. [ ] [ID: P1-CPP-REDUCE-02-S3] 例外（緊急 hotfix）時の暫定運用と後追い抽出期限を定義する。

## P1: コンパイラ共通層への抽出（py2cpp 偏在解消）

文脈: `docs-jp/plans/p1-compiler-shared-extraction.md`（`TG-P1-COMP-SHARED`）

1. [ ] [ID: P1-COMP-01] import グラフ解析（`_analyze_import_graph`）を `src/pytra/compiler/` 配下の共通モジュールへ抽出する。
2. [ ] [ID: P1-COMP-02] module EAST map 構築（`build_module_east_map`）を共通 API 化し、`py2cpp.py` 以外から再利用可能にする。
3. [ ] [ID: P1-COMP-03] module symbol index / type schema 構築（`build_module_symbol_index`, `build_module_type_schema`）を共通 API 化する。
4. [ ] [ID: P1-COMP-04] deps dump（`dump_deps_text`, `dump_deps_graph_text`）を共通 API 化し、CLI 層は表示/出力だけを担当する構成にする。
5. [ ] [ID: P1-COMP-05] 共通抽出後、`py2cpp.py` は C++ 固有責務（C++ runtime/header/multi-file 出力）へ限定する。
6. [ ] [ID: P1-COMP-09] `py2cpp.py` に残る汎用 helper（例: 文字列リスト整列、module 解析補助）を `src/pytra/compiler/` へ移管し、非 C++ 各 `py2*` から同一実装を再利用できる状態にする。
7. [ ] [ID: P1-COMP-10] 「全言語 selfhost を阻害しない共通層優先」の運用ルールを整備し、`py2cpp.py` へ汎用処理が再流入しない回帰チェック（lint/静的検査または CI ルール）を追加する。
8. [ ] [ID: P1-COMP-11] `src/pytra/compiler/transpile_cli.py` の汎用 helper 群を機能グループごとに `class + @staticmethod` へ整理し、`py2cpp.py` 側 import を class 単位へ縮退する。移行時はトップレベル互換ラッパーを暫定維持し、`tools/prepare_selfhost_source.py` / `test/unit/test_prepare_selfhost_source.py` の抽出ロジックも同時更新して selfhost 回帰を防ぐ。

進捗メモ:
- 詳細ログは `docs-jp/plans/p1-compiler-shared-extraction.md` の `決定ログ` を参照。

## P1: 多言語ランタイム配置統一

文脈: `docs-jp/plans/p1-runtime-layout-unification.md`（`TG-P1-RUNTIME-LAYOUT`）

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

文脈: `docs-jp/plans/p1-multilang-output-quality.md`（`TG-P1-MULTILANG-QUALITY`）

1. [ ] [ID: P1-MQ-01] `sample/{rs,cs,js,ts,go,java,swift,kotlin}` の生成品質を計測し、`sample/cpp` 比での差分（過剰 `mut` / 括弧 / cast / clone / 未使用 import）を定量化する。
2. [ ] [ID: P1-MQ-02] 各言語 emitter/hooks/profile に段階的改善を入れ、`sample/cpp` と同等の可読性水準へ引き上げる。
3. [ ] [ID: P1-MQ-03] 多言語の出力品質回帰を防ぐ検査（品質指標 + transpile/smoke）を整備する。
4. [ ] [ID: P1-MQ-04] 非 C++ 各言語（`rs/cs/js/ts/go/java/swift/kotlin`）で、`py2<lang>.py` の selfhost 可否（自己変換した生成物で `sample/py` を再変換できるか）を検証し、言語別ステータスを記録する。
5. [ ] [ID: P1-MQ-05] 非 C++ 各言語で、生成物による再自己変換（多段 selfhost）が成立するかを検証し、失敗要因を分類する。
6. [ ] [ID: P1-MQ-06] 非 C++ 言語の selfhost / 多段 selfhost 検証を定期実行できるチェック導線（手順またはスクリプト）を整備する。
7. [ ] [ID: P1-MQ-07] `sample/` 生成物はタイムスタンプ埋め込みなしで管理し、CI で再生成差分ゼロ（常に最新）を必須化する。

## P2: Any/object 境界整理

文脈: `docs-jp/plans/p2-any-object-boundary.md`（`TG-P2-ANY-OBJ`）

1. [ ] [ID: P2-ANY-01] `CodeEmitter` の `Any/dict` 境界を selfhost でも安定する実装へ段階移行する。
2. [ ] [ID: P2-ANY-02] `cpp_type` と式描画で `object` へのフォールバックを最小化する。
3. [ ] [ID: P2-ANY-03] `Any -> object` が必要な経路と不要な経路を分離し、過剰な `make_object(...)` 挿入を削減する。
4. [ ] [ID: P2-ANY-04] `py_dict_get_default` / `dict_get_node` の既定値が `object` 必須化している箇所を整理する。
5. [ ] [ID: P2-ANY-05] `py2cpp.py` で既定値に `nullopt` を渡している箇所を洗い出し、型別既定値へ置換する。
6. [ ] [ID: P2-ANY-06] selfhost 変換で `std::any` を通る経路を記録・列挙し、段階的に除去する。
7. [ ] [ID: P2-ANY-07] 影響上位3関数単位でパッチを分けて改善し、毎回 `check_py2cpp_transpile.py` を実行する。

## P3: microgpt 原本保全（低優先）

文脈: `docs-jp/plans/p3-microgpt-source-preservation.md`（`TG-P3-MICROGPT-SOURCE-PRESERVATION`）

1. [x] [ID: P3-MSP-01] `archive/exec-extracted-20260222.log` で抽出した原本改変項目（型注釈追加、内包/zip 展開、I/O 置換、アルゴリズム簡略化）を、parser/emitter/runtime の責務へ再分類する。
2. [x] [ID: P3-MSP-02] `materials/refs/microgpt/microgpt-20260222.py` を無改変で `py2cpp` に入力したときの失敗要因を再現・列挙し、改変で迂回していた箇所を実装タスクへ置き換える。
3. [ ] [ID: P3-MSP-03] `work/tmp/microgpt-20260222-lite.py` 依存を縮退し、原本 `materials/refs/microgpt/microgpt-20260222.py` で transpile -> `g++ -fsyntax-only` が通る回帰導線を整備する。
4. [x] [ID: P3-MSP-04] parser: 無注釈引数（`def f(x): ...`）と class 内 1 行メソッド定義（`def f(...): return ...`）の受理方針を再検討し、原本改変なしで読める範囲を拡張する。
5. [x] [ID: P3-MSP-05] parser: top-level `for` / tuple 同時代入 / 複数 `for` 内包の受理・lower を段階対応し、原本スクリプト構造を維持して EAST 化できるようにする。
6. [x] [ID: P3-MSP-06] EAST/emitter: 内包内 `range(...)` の lower 不整合（`unexpected raw range Call in EAST`）を解消する。
7. [x] [ID: P3-MSP-07] EAST/emitter: `zip` / 内包経由で `object receiver` エラーへ落ちる型崩れ経路を再現し、型解決を安定化する。
8. [x] [ID: P3-MSP-08] runtime/std: `open` 反復、`list.index`、`random.shuffle(list[str])` など原本依存 API の互換差分を整理し、どのレイヤで吸収するかを確定する。
9. [x] [ID: P3-MSP-09] 回帰導線: 原本 `materials/refs/microgpt/microgpt-20260222.py` を固定入力として、`py2cpp` 失敗要因の再発を検知する手順またはテストを追加する。

進捗メモ:
- 詳細ログは `docs-jp/plans/p3-microgpt-source-preservation.md` の `決定ログ` を参照。

## P3: Pythonic 記法戻し（低優先）

文脈: `docs-jp/plans/p3-pythonic-restoration.md`（`TG-P3-PYTHONIC`）

### `src/py2cpp.py`

1. [ ] [ID: P3-PY-01] `while i < len(xs)` + 手動インデックス更新を `for x in xs` / `for i, x in enumerate(xs)` へ戻す。
2. [x] [ID: P3-PY-02] `text[0:1] == "x"` のような1文字比較を、selfhost 要件を満たす範囲で `text.startswith("x")` へ戻す。
3. [ ] [ID: P3-PY-03] 空 dict/list 初期化後の逐次代入（`out = {}; out["k"] = v`）を、型崩れしない箇所から辞書リテラルへ戻す。
4. [ ] [ID: P3-PY-04] 三項演算子を回避している箇所（`if ...: a=x else: a=y`）を、selfhost 側対応後に式形式へ戻す。
5. [ ] [ID: P3-PY-05] import 解析の一時変数展開（`obj = ...; s = any_to_str(obj)`）を、型安全が確保できる箇所から簡潔化する。

進捗メモ:
- 詳細ログは `docs-jp/plans/p3-pythonic-restoration.md` の `決定ログ` を参照。

### `src/pytra/compiler/east_parts/code_emitter.py`

1. [x] [ID: P3-CE-01] `split_*` / `normalize_type_name` 周辺の index ループを段階的に `for` ベースへ戻す。
2. [x] [ID: P3-CE-02] `any_*` 系ヘルパで重複する `None`/空文字判定を共通小関数へ集約する。
3. [x] [ID: P3-CE-03] `_emit_trivia_items` の directive 処理分岐を小関数に分割する。
4. [x] [ID: P3-CE-04] `hook_on_*` 系で同型の呼び出しパターンを汎用ヘルパ化し、重複を減らす。

進捗メモ:
- 詳細ログは `docs-jp/plans/p3-pythonic-restoration.md` の `決定ログ` を参照。

### 作業ルール

1. [ ] [ID: P3-RULE-01] 1パッチで戻す範囲は 1〜3 関数に保つ。
2. [ ] [ID: P3-RULE-02] 各パッチで `python3 tools/check_py2cpp_transpile.py` を実行する。
3. [ ] [ID: P3-RULE-03] 各パッチで `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented` を実行する。
4. [ ] [ID: P3-RULE-04] 回帰が出た場合は「可読性改善より selfhost 安定」を優先する。

## P3: サンプル実行時間の再計測とREADME更新（低優先）

文脈: `docs-jp/plans/p3-sample-benchmark-refresh.md`（`TG-P3-SAMPLE-BENCHMARK`）

1. [ ] [ID: P3-SB-01] サンプルコード変更（実行時間変化）、サンプル番号再編（04/15/17/18）、サンプル数増加（01〜18）を反映するため、全ターゲット言語（Python/C++/Rust/C#/JS/TS/Go/Java/Swift/Kotlin）で実行時間を再計測し、トップページの `readme.md` / `readme-jp.md` の比較表を同一データで更新する。

## メモ

- このファイルは未完了タスクのみを保持します。
- 完了済みタスクは `docs-jp/todo-history/index.md` 経由で履歴へ移動します。
- `docs-jp/todo-history/index.md` は索引のみを保持し、履歴本文は `docs-jp/todo-history/YYYYMMDD.md` に日付単位で保存します。
