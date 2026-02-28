# TODO（未完了）

> `docs/ja/` が正（source of truth）です。`docs/en/` はその翻訳です。

<a href="../../en/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-02-27

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

### P0: EAST3最適化層の強化（sample C++ 出力改善）

文脈: [docs/ja/plans/p0-east3-optimizer-sample-cpp-strengthening.md](../plans/p0-east3-optimizer-sample-cpp-strengthening.md)

1. [x] [ID: P0-EAST3-OPT-SAMPLE-CPP-01] `sample/cpp` 出力で目立つ冗長構文・型変換ノイズを削減するため、EAST3最適化層を7項目で段階強化する。
2. [x] [ID: P0-EAST3-OPT-SAMPLE-CPP-01-S1-01] `RangeForCanonicalizationPass` を拡張し、`step` 定数かつ有効範囲で `stop` 非定数ケースも `StaticRangeForPlan` へ正規化する。
3. [x] [ID: P0-EAST3-OPT-SAMPLE-CPP-01-S1-02] `enumerate(list[T])` を typed iterable として扱う EAST3 正規化を追加し、`object + py_at + py_to` 連鎖の発生を抑制する。
4. [x] [ID: P0-EAST3-OPT-SAMPLE-CPP-01-S1-03] 数値式の cast-chain 縮退 pass を追加し、型既知式での冗長 `py_to<T>` を削減する。
5. [x] [ID: P0-EAST3-OPT-SAMPLE-CPP-01-S1-04] ループ不変な分母・型変換（`py_to<float64>(width)` 等）の preheader hoist を追加し、内側ループの変換負荷を削減する。
6. [x] [ID: P0-EAST3-OPT-SAMPLE-CPP-01-S1-05] `list[list[int64]]` など型既知 `py_repeat` 初期化を typed materialization へ正規化し、`make_object(py_repeat(...))` 経路を縮退する。
7. [x] [ID: P0-EAST3-OPT-SAMPLE-CPP-01-S1-06] `dict<str, V>` の key アクセス/代入で不要な `py_to_string` を削減する EAST3 正規化を追加する。
8. [x] [ID: P0-EAST3-OPT-SAMPLE-CPP-01-S1-07] tuple unpack に対する一時 tuple 変数の生成を抑制し、`TupleTarget` 直接展開へ寄せる最適化を追加する。
- `P0-EAST3-OPT-SAMPLE-CPP-01-S1-01` `RangeForCanonicalizationPass` を拡張し、`range(n)`（`n: int64`）の `stop` 非定数ケースを `StaticRangeForPlan` へ正規化できることを `test_east3_optimizer.py` で回帰固定した。
- `P0-EAST3-OPT-SAMPLE-CPP-01-S1-02` `TypedEnumerateNormalizationPass` を追加し、`enumerate(list[T])` の `iter_item_type` / `iter_element_type` / `target_plan` 型情報を補完して typed loop header を選べることを `test_east3_optimizer.py` / `test_east3_cpp_bridge.py` で回帰固定した。
- `P0-EAST3-OPT-SAMPLE-CPP-01-S1-03` `NumericCastChainReductionPass` を追加し、同型 `static_cast` / `Unbox` の冗長連鎖を fail-closed で縮退できることを `test_east3_optimizer.py` で回帰固定した。
- `P0-EAST3-OPT-SAMPLE-CPP-01-S1-04` `LoopInvariantCastHoistPass` を追加し、`BinOp` の右辺数値昇格 cast を preheader へ hoist して `sample/06` の `height-1`/`width-1`/`frames_n` 変換をループ外へ移動できることを回帰固定した。
- `P0-EAST3-OPT-SAMPLE-CPP-01-S1-05` `TypedRepeatMaterializationPass` を追加し、`[0] * w` 系 `ListComp` の型を `list[list[int64]]` へ補完して `sample/py` 再変換で `make_object(py_repeat(...))` を 0 件化した。
- `P0-EAST3-OPT-SAMPLE-CPP-01-S1-06` `DictStrKeyNormalizationPass` を追加し、`dict[str, V]` キーを `dict_key_verified` 付きで正規化して `sample/18` の `env[...]` 経路から不要な `py_to_string` を除去しつつ `check_py2cpp_transpile.py` を通過させた。

### P0: Ruby `/` 演算の真の除算互換修正（最優先）

文脈: [docs/ja/plans/p0-ruby-true-division-parity.md](../plans/p0-ruby-true-division-parity.md)

1. [x] [ID: P0-RUBY-DIV-SEMANTICS-01] Ruby backend の `/` lowering を Python 互換（true division）へ修正し、`int/int` 由来の意味差を解消する。
2. [x] [ID: P0-RUBY-DIV-SEMANTICS-01-S1-01] `sample/06` を含む回帰ケースで現象再現を固定化し、ユニット/スモークで `/` の意味差を検知できるテストを追加する。
3. [x] [ID: P0-RUBY-DIV-SEMANTICS-01-S1-02] Ruby emitter の二項演算 lower を修正し、Python の `/` を常に真の除算として出力する（必要に応じて型変換 helper を追加）。
4. [x] [ID: P0-RUBY-DIV-SEMANTICS-01-S1-03] `sample/ruby` 再生成と parity 再検証（特に `sample/06`）を実施し、README 計測値の妥当性確認手順を文書へ反映する。

### P1: sample/18 C++ 生成コードの可読性縮退（選定: #2,#7,#8,#5,#1）

文脈: [docs/ja/plans/p1-cpp-sample18-readability-slimming.md](../plans/p1-cpp-sample18-readability-slimming.md)

1. [x] [ID: P1-CPP-S18-READ-01] `sample/18` の C++ 生成コードについて、選定改善項目（#2,#7,#8,#5,#1）を段階適用し、可読性を上げつつ挙動互換を維持する。
2. [x] [ID: P1-CPP-S18-READ-01-S1-02] 改善項目 #2: tuple unpack / 一時変数周辺の冗長 cast (`py_cast` / `py_to_*`) を削減し、型既知経路で直接利用できる emit に寄せる。
3. [x] [ID: P1-CPP-S18-READ-01-S1-07] 改善項目 #7: `map` キーアクセス時の不要な key 変換（`py_to_string` 連鎖など）を縮退し、同一キー型では直接アクセスを優先する。
4. [x] [ID: P1-CPP-S18-READ-01-S1-08] 改善項目 #8: 計測/時刻差分まわりの変換コードを簡約し、冗長な数値変換チェーンを減らす。
5. [x] [ID: P1-CPP-S18-READ-01-S1-05] 改善項目 #5: `unknown` 起点の過剰な default 初期化・型減衰を抑え、可能な範囲で宣言型を安定化する。
6. [x] [ID: P1-CPP-S18-READ-01-S1-01] 改善項目 #1: `ForCore(RuntimeIterForPlan)` の typed loop header 化（`P0-FORCORE-TYPE-01-S3-01` と整合）を可読性改善セットへ統合する。
- `P1-CPP-S18-READ-01-S1-02` `ForCore(RuntimeIterForPlan)+NameTarget` で typed iterable を優先する emit を追加し、`sample/18` の `for stmt in stmts` から `object __itobj + obj_to_rc_or_raise` を除去した。
- `P1-CPP-S18-READ-01-S1-07` `dict_key_verified` key の load/store 回帰テストを追加し、`sample/18` 再生成で `env[py_to_string(...)]` ではなく `env[stmt->name]` を維持できることを固定した。
- `P1-CPP-S18-READ-01-S1-08` `perf_counter` の `resolved_type=float64` を固定して不要 `Unbox` を縮退し、`sample/18` の `start/elapsed` で `py_to<float64>` 連鎖を除去した。
- `P1-CPP-S18-READ-01-S1-05` return 経路で空 collection literal を既知戻り値型へ寄せる補正を追加し、`sample/18` の `new_expr_nodes()` を `list<rc<ExprNode>>{}` へ安定化した。

### P1: Go/Java/Swift/Ruby runtime 外出し（inline helper 撤去）

文脈: [docs/ja/plans/p1-runtime-externalization-gjsr.md](../plans/p1-runtime-externalization-gjsr.md)

1. [ ] [ID: P1-RUNTIME-EXT-01] Go/Java/Swift/Ruby の生成コードから `__pytra_*` runtime helper の inline 定義を撤去し、言語別 runtime ファイル参照へ統一する。
2. [ ] [ID: P1-RUNTIME-EXT-01-S1-01] 現行 emitter が inline 出力している helper 群を言語別に棚卸しし、runtime 側 API（正本）との対応表を固定する。
3. [ ] [ID: P1-RUNTIME-EXT-01-S2-01] Go backend を runtime 外部参照方式へ移行し、`py2go` 出力から helper 本体を除去する。
4. [ ] [ID: P1-RUNTIME-EXT-01-S2-02] Java backend を runtime 外部参照方式へ移行し、`py2java` 出力から helper 本体を除去する。
5. [ ] [ID: P1-RUNTIME-EXT-01-S2-03] Swift backend 用の native runtime ファイルを整備し、`py2swift` 出力から helper 本体を除去する。
6. [ ] [ID: P1-RUNTIME-EXT-01-S2-04] Ruby backend 用 runtime ファイルを新設し、`py2rb` 出力から helper 本体を除去する。
7. [ ] [ID: P1-RUNTIME-EXT-01-S3-01] `runtime_parity_check` / smoke テスト / sample 再生成導線を runtime 外部参照前提に更新し、回帰を固定する。

### P1: 統合CLI `./pytra` の Rust target 追加

文脈: [docs/ja/plans/p1-pytra-cli-rs-target.md](../plans/p1-pytra-cli-rs-target.md)

1. [ ] [ID: P1-PYTRA-CLI-RS-01] 統合CLI `./pytra` に `--target rs` を追加し、Rust 変換を C++ と同じ入口で実行可能にする。
2. [ ] [ID: P1-PYTRA-CLI-RS-01-S1-01] `src/pytra/cli.py` の target dispatch を拡張し、`--target rs` で `py2rs.py` を呼び出せるようにする。
3. [ ] [ID: P1-PYTRA-CLI-RS-01-S1-02] Rust 出力時の `--output` / `--output-dir` の挙動を確定し、拡張子と出力先衝突を整理する。
4. [ ] [ID: P1-PYTRA-CLI-RS-01-S1-03] `docs/ja/how-to-use.md` の統合CLI節に Rust 例を追加し、`out/` / `/tmp` の一時出力運用を明記する。

### P4: 全言語 selfhost 完全化（低低優先）

文脈: [docs/ja/plans/p4-multilang-selfhost-full-rollout.md](../plans/p4-multilang-selfhost-full-rollout.md)

1. [ ] [ID: P4-MULTILANG-SH-01] `cpp/rs/cs/js/ts/go/java/swift/kotlin` の selfhost を段階的に成立させ、全言語の multistage 監視を通過可能にする。
2. [x] [ID: P4-MULTILANG-SH-01-S1-01] 現状の stage1/stage2/stage3 未達要因を言語別に固定化し、優先順（blocking chain）を明文化する。
3. [x] [ID: P4-MULTILANG-SH-01-S1-02] multistage runner 未定義言語（go/java/swift/kotlin）の runner 契約を定義し、`runner_not_defined` を解消する実装方針を確定する。
4. [x] [ID: P4-MULTILANG-SH-01-S2-01] Rust selfhost の stage1 失敗（from-import 受理）を解消し、stage2 へ進める。
5. [ ] [ID: P4-MULTILANG-SH-01-S2-02] C# selfhost の stage2 compile 失敗を解消し、stage3 変換を通す。
6. [x] [ID: P4-MULTILANG-SH-01-S2-02-S1] C# emitter の selfhost 互換ギャップ（`Path`/`str.endswith|startswith`/定数デフォルト引数）を埋め、先頭 compile エラーを前進させる。
7. [ ] [ID: P4-MULTILANG-SH-01-S2-02-S2] `py2cs.py` selfhost 生成物の import 依存解決方針（単体 selfhost source 生成 or モジュール連結）を確定し、`sys/argparse/transpile_cli` 未解決を解消する。
8. [x] [ID: P4-MULTILANG-SH-01-S2-02-S2-S1] C# selfhost 先頭エラーの足切り（`sys.exit` / docstring式）を解消し、import 依存未解決の先頭シンボルを確定する。
9. [ ] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2] C# selfhost 用の import 依存閉包方式（単体 selfhost source 生成 or モジュール連結）を実装し、`transpile_to_csharp` 未解決を解消する。
10. [x] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2-S1] 単体 selfhost source 方式の PoC（`prepare_selfhost_source_cs.py`）を実装し、変換可否を実測で確認する。
11. [ ] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2-S2] PoC 失敗要因（C# object receiver 制約）を解消するか、モジュール連結方式へ pivot して import 依存閉包を成立させる。
12. [x] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S1] 単体 selfhost source PoC の parse 制約（object receiver access）を解消し、`selfhost/py2cs.py` の C# 変換を通す。
13. [ ] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2] 単体 selfhost source 生成物（`cs_selfhost_full_stage1.cs`）の compile 失敗を分類し、mcs 通過に必要な emit/runtime 互換ギャップを埋める。
14. [x] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S1] compile 失敗の機械分類ツールを追加し、エラーコード/カテゴリの現状値をレポート化する。
15. [x] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S2] 分類結果（テンプレート断片混入 / 呼び出し形状崩れ / shadowed local）に対応する修正を実装し、`CS1525/CS1002` を段階的に削減する。
16. [x] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S3] `mcs` 内部例外（`tuples > 7`）を回避する emit 方針を実装し、stage2 compile を次段検証可能な状態へ戻す。
17. [x] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S4] `mcs` で顕在化した通常 compile エラー（`CS1061/CS0103/CS1503` 上位群）の先頭カテゴリを削減し、stage2 失敗件数を継続的に縮退させる。
18. [x] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S5] 残存上位エラー（`CS0103 set/list/json` と `CS0019 char/string`）を対象に emitter lower を追加し、stage2 compile 失敗件数をさらに縮退させる。
19. [x] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S6] 残存の主要失敗（`json` 未解決、`dict.get/items` 未lower、`CodeEmitter` static参照不整合）を段階解消し、stage2 compile の上位エラー構成を更新する。
20. [ ] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7] 残存上位エラー（`_add`/`item_expr` の未定義、`object` 由来の `CS1503/CS0266`）を対象に nested helper/型縮約を補強し、stage2 compile 件数をさらに削減する。
21. [ ] [ID: P4-MULTILANG-SH-01-S2-02-S3] C# selfhost の stage2/stage3 を通し、`compile_fail` から `pass` へ到達させる。
22. [ ] [ID: P4-MULTILANG-SH-01-S2-03] JS selfhost の stage2 依存 transpile 失敗を解消し、multistage を通す。
23. [ ] [ID: P4-MULTILANG-SH-01-S3-01] TypeScript の preview-only 状態を解消し、selfhost 実行可能な生成モードへ移行する。
24. [ ] [ID: P4-MULTILANG-SH-01-S3-02] Go/Java/Swift/Kotlin の native backend 化タスクと接続し、selfhost 実行チェーンを有効化する。
25. [ ] [ID: P4-MULTILANG-SH-01-S4-01] 全言語 multistage 回帰を CI 導線へ統合し、失敗カテゴリの再発を常時検知できるようにする。
26. [ ] [ID: P4-MULTILANG-SH-01-S4-02] 完了判定テンプレート（各言語の stage 通過条件と除外条件）を文書化し、運用ルールを固定する。
- `P4-MULTILANG-SH-01-S1-01` `check_multilang_selfhost_suite.py` を再実行し、`rs/cs/js/ts/go/java/swift/kotlin` の stage1/2/3 未達カテゴリと先頭原因を `docs/ja/plans/p4-multilang-selfhost-full-rollout.md` に固定した。
- `P4-MULTILANG-SH-01-S1-02` `go/java/swift/kotlin` の runner 契約（build/run と fail 分類）を `docs/ja/plans/p4-multilang-selfhost-full-rollout.md` に確定した。
- `P4-MULTILANG-SH-01-S2-01` `src/py2rs.py` の括弧付き `from-import` を解消し、`rs` の stage1 を pass（次段は `compile_fail`）へ遷移させた。
- `P4-MULTILANG-SH-01-S2-02-S1` C# emitter で `Path`/`str.endswith|startswith`/定数デフォルト引数を selfhost 互換化し、`cs` の先頭 compile エラーを `Path` 未解決から `sys` 未解決へ前進させた。
- `P4-MULTILANG-SH-01-S2-02-S2-S1` `sys.exit` lower と docstring式除去を入れ、`cs` の先頭 compile エラーを `transpile_to_csharp` 未解決へ前進させた。
- `P4-MULTILANG-SH-01-S2-02-S2-S2-S1` `prepare_selfhost_source_cs.py` を追加して単体 selfhost source を検証し、C# object receiver 制約で現状は不成立と固定した。
- `P4-MULTILANG-SH-01-S2-02-S2-S2-S1` hook 無効化パッチを追加しても `CSharpEmitter._walk_node_names` の `node.get(...)` で同制約違反が継続することを確認し、PoC阻害要因を具体化した。
- `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S1` `CSharpEmitter._walk_node_names` の `Any` 直アクセスを helper 化し、`selfhost/py2cs.py` の C# 変換を通過させた（次段は compile fail）。
- `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S1` `check_cs_single_source_selfhost_compile.py` を追加し、`p4-cs-single-source-selfhost-compile-status.md` で compile 失敗の件数分類（`CS1525/CS1002` 中心）を固定した。
- `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S2` C# emitter の `JoinedStr`/`Set` lower・optional 引数順序・ローカル shadow 回避を実装し、`test/unit/test_py2cs_smoke.py`（26件）を通過。`check_cs_single_source_selfhost_compile.py` で `CS1525/CS1002` が 0 件化し、次ブロッカーが `mcs tuples > 7` 内部例外に収束した。
- `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S3` tuple arity が `1` または `>7` のとき `List<object>` へ lower する C# emitter 修正を追加し、`test/unit/test_py2cs_smoke.py`（28件）を通過。`check_cs_single_source_selfhost_compile.py` で `mcs tuples > 7` 内部例外が解消し、失敗モードを通常の compile エラー（`CS1061/CS0103/CS1503` など）へ遷移させた。
- `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S4` C# class 定義に base 句（`class Child : Base`）を出力するよう修正し、継承欠落による `CS1061` を大幅削減。`check_cs_single_source_selfhost_compile.py` で `CS1061` を `469 -> 109` に縮退させ、`test/unit/test_py2cs_smoke.py` を 29 件で通過させた。
- `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S5` `set/list/dict` の型ヒント連動 lower、`for ch in str` の string 化、`strip/find/rfind/replace` lower を追加し、`test/unit/test_py2cs_smoke.py` を 32 件で通過。`check_cs_single_source_selfhost_compile.py` で `CS1061` を `109 -> 20`、`CS0103` を `81 -> 36` に縮退させた。
- `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S6` `@staticmethod/@classmethod` の static 出力、`json.loads` lower、`dict.get/items` の unknown 型フォールバックを追加し、`check_cs_single_source_selfhost_compile.py` で `CS0120` を `5 -> 0`、`CS1061` を `20 -> 10`、`CS0103` を `36 -> 34` に縮退させた。
- `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7` `_collect_using_lines` のローカル helper をクラスメソッド化し、`_emit_assign` の `item_expr` 初期化を追加。`check_cs_single_source_selfhost_compile.py` で `CS0103` を `34 -> 12` に縮退させた（`CS1503/CS0266` は継続対応）。
- `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7` keyword 引数呼び出し崩れ対策（`code_emitter`/`cs_emitter`/`transpile_cli`）、`py2cs.py` の argparse 依存除去、`prepare_selfhost_source(_cs).py` の補助生成を追加し、`check_cs_single_source_selfhost_compile.py` で `CS0103` を `12 -> 1`、`CS0815` を `5 -> 3` まで縮退させた（`CS1502/CS1503/CS0266` は継続対応）。
