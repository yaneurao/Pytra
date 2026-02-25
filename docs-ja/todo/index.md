# TODO（未完了）

> `docs-ja/` が正（source of truth）です。`docs/` はその翻訳です。

<a href="../../docs/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-02-25

## 文脈運用ルール

- 各タスクは `ID` と文脈ファイル（`docs-ja/plans/*.md`）を必須にする。
- 優先度上書きは `docs-ja/plans/instruction-template.md` 形式でチャット指示し、`todo2.md` は使わない。
- 着手対象は「未完了の最上位優先度ID（最小 `P<number>`、同一優先度では上から先頭）」に固定し、明示上書き指示がない限り低優先度へ進まない。
- `P0` が 1 件でも未完了なら `P1` 以下には着手しない。
- 着手前に文脈ファイルの `背景` / `非対象` / `受け入れ基準` を確認する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める（例: ``[ID: P0-XXX-01] ...``）。
- `docs-ja/todo/index.md` の進捗メモは 1 行要約に留め、詳細（判断・検証ログ）は文脈ファイル（`docs-ja/plans/*.md`）の `決定ログ` に記録する。
- 1 つの `ID` が大きい場合は、文脈ファイル側で `-S1` / `-S2` 形式の子タスクへ分割して進めてよい（親 `ID` 完了までは親チェックを維持）。
- 割り込み等で未コミット変更が残っている場合は、同一 `ID` を完了させるか差分を戻すまで別 `ID` に着手しない。
- `docs-ja/todo/index.md` / `docs-ja/plans/*.md` 更新時は `python3 tools/check_todo_priority.py` を実行し、差分に追加した進捗 `ID` が最上位未完了 `ID`（またはその子 `ID`）と一致することを確認する。
- 作業中の判断は文脈ファイルの `決定ログ` へ追記する。



## メモ

- このファイルは未完了タスクのみを保持します。
- 完了済みタスクは `docs-ja/todo/archive/index.md` 経由で履歴へ移動します。
- `docs-ja/todo/archive/index.md` は索引のみを保持し、履歴本文は `docs-ja/todo/archive/YYYYMMDD.md` に日付単位で保存します。

## P0: isinstance 判定を type_id 区間判定へ統一（最優先）

文脈: `docs-ja/plans/p0-isinstance-single-inheritance.md`（`P0-ISINSTANCE-01`）

1. [x] [ID: P0-ISINSTANCE-01] 単一継承前提の `type_id_min/type_id_max` で `isinstance` を統一し、全対象言語で文字列名比較・多重継承推論・ハイブリッド分岐を排除する。
2. [x] [ID: P0-ISINSTANCE-01-S1] C++/JS/TS/RS/CS の `isinstance` lower を `py_isinstance`/`py_is_subtype` 系 API に置換する。
3. [x] [ID: P0-ISINSTANCE-01-S2] 多重継承を要求する入力（複数基底）を compile-time で検出し、明示エラーへ統一する。
4. [x] [ID: P0-ISINSTANCE-01-S3] runtime 側 `type_id` 範囲テーブルを検証し、`expected.min <= actual <= expected.max` 判定の観測不変性を回帰テスト化する。
5. [x] [ID: P0-ISINSTANCE-01-S4] 既存 `isinstance` テストを更新・追加し、`tools/check_*_transpile.py` と `test/unit` の回帰条件を全言語で再固定化する。
6. [x] [ID: P0-ISINSTANCE-01-S5] `docs-ja/spec/spec-type_id.md`（必要なら `docs-ja/spec/spec-linker.md`）への最終整合を確認したうえで、関連タスクの完了条件を反映する。
- `P0-ISINSTANCE-01`: `self_hosted` パーサで複数基底クラスを明示エラー化し、C++/JS/TS/RS/CS の `isinstance` lower/runtime 棚卸し結果を `docs-ja/plans/p0-isinstance-single-inheritance.md` へ記録した。
- `P0-ISINSTANCE-01`: `src/pytra/built_in/type_id.py` と JS/TS runtime を `type_id` 範囲テーブル（order/min/max）判定へ移行し、`test_pytra_built_in_type_id.py` と `test_js_ts_runtime_dispatch.py` へ sibling 非包含の回帰を追加した。
- `P0-ISINSTANCE-01`: C# emitter の `isinstance` lower を `py_isinstance` API 呼び出しへ統一し、`runtime/cs` に `PYTRA_TID_*` / `py_runtime_type_id` / `py_is_subtype` / `py_isinstance` を追加、`test_py2cs_smoke.py` で回帰固定した。
- `P0-ISINSTANCE-01`: Rust emitter を `py_isinstance(&x, <type_id>)` lower + `type_id` 範囲テーブル出力へ移行し、`test_py2rs_smoke.py`（22件）/`tools/check_py2rs_transpile.py`（`checked=130 ok=130`）と `tools/check_py2{cpp,cs,js,ts}_transpile.py`（JS/TS は `--skip-east3-contract-tests` で `checked=130 ok=130`）で回帰を確認した。
- `P0-ISINSTANCE-01`: CppEmitter の EAST3 bridge 互換経路（legacy `isinstance`/builtin call/method、`dict[str,*]` key coercion、`render_cond(Any)`）を修正し、`tools/check_py2{cpp,rs,cs,js,ts}_transpile.py` と `isinstance` 関連 unit を通常モードで再固定化した。
- `P0-ISINSTANCE-01-S5`: `docs-ja/spec/spec-type_id.md` の Codegen 規約へ `east_stage=3` strict 拒否条件と `east_stage=2 + self_hosted` 互換層の位置づけを追記し、実装との最終整合を反映した。

## P0: サンプル全言語のゴールデン一致パイプライン（最優先）

文脈: `docs-ja/plans/p0-sample-all-languages-golden-pipeline.md`（`P0-SAMPLE-GOLDEN-ALL-01`）

1. [ ] [ID: P0-SAMPLE-GOLDEN-ALL-01] `sample/py` の 18 件を `cpp/rs/cs/js/ts/go/java/swift/kotlin` 全言語でコンパイル→実行→`sample/golden/manifest.json` との一致まで到達する（失敗カテゴリ別に順次修正する）。
2. [x] [ID: P0-SAMPLE-GOLDEN-ALL-01-S1] 検証対象の固定化（サンプル18件・言語9件・比較ルール）を行い、再現可能な共通実行手順を文書化する。
3. [x] [ID: P0-SAMPLE-GOLDEN-ALL-01-S2] runtime parity 実行フローを全言語対応に整備し、`tools/runtime_parity_check.py` の到達条件（toolchain、入出力、失敗分類）を実運用で安定化する。
4. [x] [ID: P0-SAMPLE-GOLDEN-ALL-01-S3] C++ 18件の compile/run/compare を完全一致状態へ戻す。
5. [x] [ID: P0-SAMPLE-GOLDEN-ALL-01-S4] Rust 18件を compile/run/compare 完全一致へ。
6. [x] [ID: P0-SAMPLE-GOLDEN-ALL-01-S5] C# 18件を compile/run/compare 完全一致へ。
7. [x] [ID: P0-SAMPLE-GOLDEN-ALL-01-S6] JS/TS 18件を transpile/run/compare 完全一致へ。
8. [ ] [ID: P0-SAMPLE-GOLDEN-ALL-01-S7] Go/Java/Swift/Kotlin 18件を transpile/run/compare 完全一致へ。
9. [ ] [ID: P0-SAMPLE-GOLDEN-ALL-01-S8] 全言語最終結果を `readme-ja.md` / `readme.md` のサンプル実行結果へ反映し、`golden` 差分が発生しない運用を維持する。
- `P0-SAMPLE-GOLDEN-ALL-01-S1`: 検証スコープ（`sample/py` 18件・9言語）と比較ルール（stdout 正規化/artefact hash-size/source hash）、再現コマンド（`runtime_parity_check.py` / `verify_sample_outputs.py`）を文脈ファイルへ固定した。
- `P0-SAMPLE-GOLDEN-ALL-01-S2`: `runtime_parity_check.py` に `--all-samples`/`--summary-json` と失敗カテゴリ集計を追加し、`test_runtime_parity_check_cli.py` + `test_image_runtime_parity.py` で CLI 解決規約と C++ 到達性を回帰固定した。
- `P0-SAMPLE-GOLDEN-ALL-01-S3`: C++ emitter の module namespace/include 解決（`math/time` と `pytra.runtime -> pytra.utils`）と runtime tuple boxing/type_id 初期化順序を修正し、`runtime_parity_check.py --case-root sample --targets cpp --ignore-unstable-stdout` で 18/18 pass を固定した。
- `P0-SAMPLE-GOLDEN-ALL-01-S4`: Rust emitter の call/subscript/dict/class mutability lower を修正し、`runtime_parity_check.py --case-root sample --targets rs --all-samples --ignore-unstable-stdout` で `SUMMARY cases=18 pass=18 fail=0 targets=rs` を確認した。
- `P0-SAMPLE-GOLDEN-ALL-01-S5`: C# emitter/runtime（import解決、listcomp/range、bytes/tuple/slice lower、dataclass ctor、math/time/pathlib runtime）を修正し、`runtime_parity_check.py --case-root sample --targets cs --all-samples --ignore-unstable-stdout` で `SUMMARY cases=18 pass=18 fail=0 targets=cs` を確認した。
- `P0-SAMPLE-GOLDEN-ALL-01-S6`: JS emitter の import/runtime shim・list/listcomp/range/compare/builtin lower を修正し、`runtime_parity_check.py --case-root sample --targets js,ts --all-samples --ignore-unstable-stdout` で `SUMMARY cases=18 pass=18 fail=0 targets=js,ts` を確認した。
- `P0-SAMPLE-GOLDEN-ALL-01-S7`: `go/java/kotlin` は JS sidecar bridge 方式で `runtime_parity_check.py --case-root sample --targets go,java,swift,kotlin --all-samples --ignore-unstable-stdout` の `ok: 54` を確認済み（18件×3言語）。残件は `swiftc` 未導入による `toolchain_missing: 18`。

## P1: CppEmitter の pylib 互換名正規化除去（中優先）

文脈: `docs-ja/plans/p1-cpp-emitter-remove-pylib-compat.md`（`P1-CPP-EMIT-NORM-01`）

1. [x] [ID: P1-CPP-EMIT-NORM-01] `src/hooks/cpp/emitter/cpp_emitter.py` の `_normalize_runtime_module_name` を削除し、`pylib.*` 互換名を前提としない runtime module 解決へ切り替える（`P1-CPP-EMIT-NORM-01-S1` 〜 `S3` の完了でクローズ）。
2. [x] [ID: P1-CPP-EMIT-NORM-01-S1] `src/hooks/cpp/emitter/cpp_emitter.py` と `src/hooks/cpp/emitter/call.py` の該当呼び出しを洗い出し、`module_name` 正規化なしでの解決パスへ置換する。
3. [x] [ID: P1-CPP-EMIT-NORM-01-S2] `src/pytra/compiler/east_parts/code_emitter.py` の同名的な正規化利用有無を確認し、必要なら `pylib` 前提経路を削減する。
4. [x] [ID: P1-CPP-EMIT-NORM-01-S3] 回帰テスト/ドキュメントを整備し、`pylib.*` 互換を求めるケースが存在しないことを明文化する（`docs-ja/spec/spec-dev.md` 追記含む）。

## P1: CppEmitter 多重継承廃止（中優先）

文脈: `docs-ja/plans/p1-cpp-emitter-no-multiple-inheritance.md`（`P1-CPP-EMIT-NOMI-01`）

1. [x] [ID: P1-CPP-EMIT-NOMI-01] `src/hooks/cpp/emitter/cpp_emitter.py` の多重継承を廃止し、単一継承 + 明示的委譲へ切り替える。
2. [x] [ID: P1-CPP-EMIT-NOMI-01-S1] `cpp_emitter.py` の状態管理を維持しつつ、`CppCallEmitter`/`CppStatementEmitter`/`CppExpressionEmitter`/`CppBinaryOperatorEmitter`/`CppTriviaEmitter`/`CppTemporaryEmitter` のメソッドを `CppEmitter` へデリゲーション注入し、単一継承化を実現する。
3. [x] [ID: P1-CPP-EMIT-NOMI-01-S2] `CppEmitter` 単一継承移行中の `isinstance()`/型チェック関連の条件分岐を簡素化し、分岐経路を明示フラグ化する。

## P1: C++ runtime 変換ヘルパのテンプレ化（中優先）

文脈: `docs-ja/plans/p1-cpp-py_to-template.md`（`P1-CPP-PYTO-01`）

1. [ ] [ID: P1-CPP-PYTO-01] `py_to_int64 / py_to_float64 / py_to_bool` を中核に、型パラメータ化された `py_to<T>()` API を追加し、`object`/`std::any` の変換経路を破綻なく吸収しつつ呼び出しを統一する。
2. [ ] [ID: P1-CPP-PYTO-01-S1] `src/runtime/cpp/pytra-core/built_in/py_runtime.h` に `template <class T, ...> static inline T py_to(T)` 系を導入し、既存 `py_to_*` API は後方互換ラッパとして残す。
3. [ ] [ID: P1-CPP-PYTO-01-S2] `src/hooks/cpp/emitter/cpp_emitter.py` と `src/hooks/cpp/emitter/expr.py` の `py_to_int64(...)` 直接呼び出しを新 API 準拠へ段階移行する（`expr` の cast、runtime 呼び出し系で挙動差分がないことを確認）。
4. [ ] [ID: P1-CPP-PYTO-01-S3] `py_to_int64(object/any)` の例外・既定値挙動を検証し、`sample` や回帰テストで再生成差分が許容範囲かを確認して `readme-ja.md` の該当方針へ反映する。

## P2: C++ selfhost の virtual ディスパッチ簡略化（低優先）

文脈: `docs-ja/plans/p2-cpp-virtual-selfhost-dispatch.md`（`P2-CPP-SELFHOST-VIRTUAL-01`）

1. [ ] [ID: P2-CPP-SELFHOST-VIRTUAL-01] `virtual/override` ベースの selfhost クラス呼び出し経路へ縮退できる箇所を洗い出し、`type_id` 分岐を低優先で簡素化する。
2. [ ] [ID: P2-CPP-SELFHOST-VIRTUAL-01-S1-01] `rg` と AST で、`sample`/`selfhost` の class method 生成に含まれる `type_id` ベース分岐を抽出する。
3. [ ] [ID: P2-CPP-SELFHOST-VIRTUAL-01-S1-02] 抽出結果を「基底クラス呼び出し」「再帰呼び出し」「ユーティリティ呼び出し」に分類し、非対象を明文化する。
4. [ ] [ID: P2-CPP-SELFHOST-VIRTUAL-01-S1-03] `virtual` 置換候補を安全性（既存テスト影響）順で優先順位付けし、実施順を確定する。
5. [ ] [ID: P2-CPP-SELFHOST-VIRTUAL-01-S2-01] `py2cpp.py` 側 emit を切り出しして、`virtual` へ寄せる対象経路と fallback 経路を分離する。
6. [ ] [ID: P2-CPP-SELFHOST-VIRTUAL-01-S2-02] `CppEmitter` の class method 呼び出し描画で、`virtual`/`override` 有無に応じた分岐を明示化する。
7. [ ] [ID: P2-CPP-SELFHOST-VIRTUAL-01-S2-03] 置換できない `type_id` 分岐は理由付きで残し、非対象リストへ接続する。
8. [ ] [ID: P2-CPP-SELFHOST-VIRTUAL-01-S3-01] `sample` の 2〜3 件から `type_id` 分岐を `virtual` 呼び出しに移行する。
9. [ ] [ID: P2-CPP-SELFHOST-VIRTUAL-01-S3-02] 移行対象を段階的に拡大し、selfhost 再変換（`sample`/`test`）の成功率を評価する。
10. [ ] [ID: P2-CPP-SELFHOST-VIRTUAL-01-S3-03] 移行不能ケースは判定ロジックで固定し、次回に回す明細を更新する。
11. [ ] [ID: P2-CPP-SELFHOST-VIRTUAL-01-S4-01] `test/unit` と `sample` 再生成の回帰ケースを追加・更新して diff を固定する。
12. [ ] [ID: P2-CPP-SELFHOST-VIRTUAL-01-S4-02] `tools/check_selfhost_cpp_diff.py` と `tools/verify_selfhost_end_to_end.py` を再実行し、回帰条件が満たされることを確認する。
13. [ ] [ID: P2-CPP-SELFHOST-VIRTUAL-01-S4-03] `docs-ja/spec/spec-dev.md`（必要なら `spec-type_id`）へ簡潔に反映する。
14. [ ] [ID: P2-CPP-SELFHOST-VIRTUAL-01-S5-01] `test/unit` へ `Base`/`Child` の `virtual/override` 呼び出しケース（`Base.f` 明示呼び出し、`super().f`、`virtual` 期待差分）を追加し、`type_id` 分岐除去を固定する。
15. [ ] [ID: P2-CPP-SELFHOST-VIRTUAL-01-S5-02] `sample` 再変換で `type_id` 分岐が残る境界 (`staticmethod`/`class` method/`object` receiver) を明文化した回帰ケースを追加する。
16. [ ] [ID: P2-CPP-SELFHOST-VIRTUAL-01-S5-03] `tools/verify_selfhost_end_to_end.py` を使う selfhost 回帰（最低2ケース）に virtual 化前後の差分検証を追加し、再変換可能性を固定する。
