# TODO（未完了）

> `docs/ja/` が正（source of truth）です。`docs/en/` はその翻訳です。

<a href="../../en/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-02-28

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

### P1: 全言語コメント忠実性ポリシー（生成コメント禁止）

文脈: [docs/ja/plans/p1-comment-fidelity-all-backends.md](../plans/p1-comment-fidelity-all-backends.md)

1. [ ] [ID: P1-COMMENT-FIDELITY-01] 全 backend の出力で「元ソースにないコメントを禁止し、元コメントを欠落なく反映する」契約を実装とテストで固定する。
2. [ ] [ID: P1-COMMENT-FIDELITY-01-S1-01] 全 emitter の固定コメント/`TODO`/`pass` コメント出力箇所を棚卸しし、禁止パターン一覧を固定する。
3. [ ] [ID: P1-COMMENT-FIDELITY-01-S1-02] コメント出力契約（`module_leading_trivia` / `leading_trivia` のみ許可）と fail-closed 方針を仕様化する。
4. [ ] [ID: P1-COMMENT-FIDELITY-01-S2-01] `ts/go/java/swift/kotlin/ruby/lua` の固定コメント出力を撤去し、元コメント伝播のみへ統一する。
5. [ ] [ID: P1-COMMENT-FIDELITY-01-S2-02] `cpp/rs/cs/js` の `pass` / unsupported コメント経路を no-op または例外へ置換する。
6. [ ] [ID: P1-COMMENT-FIDELITY-01-S3-01] 全 `test_py2*smoke.py` に禁止コメント検査と元コメント反映テストを追加し、回帰を固定する。
7. [ ] [ID: P1-COMMENT-FIDELITY-01-S3-02] `sample/*` 再生成と差分検証を行い、固定コメント残存ゼロを確認する。

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
- `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7` `prepare_selfhost_source_cs.py` の `__main__` ガード置換を `main([str(x) for x in args])` に更新し、`check_cs_single_source_selfhost_compile.py` で `CS0103` を `1 -> 0`、`CS1503` を `61 -> 60`、`CS1502` を `47 -> 46` へ縮退させた。
- `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7` `code_emitter.py` で `EmitterHooks.to_dict` の key を `str` 化し、`_root_scope_stack` の型付き初期化を明示した。`test_py2cs_smoke.py`（34件）通過のうえ `check_cs_single_source_selfhost_compile.py` で `CS1503` を `60 -> 58`、`CS1502` を `46 -> 45`、`CS1950` を `14 -> 13` に縮退させた。
- `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7` `py2cs.py` の `_arg_get_str` 型注釈を `dict[str, str]` に整合させ、selfhost 生成物の `Dictionary<string,string>` / `Dictionary<string,object>` 混在由来の型不一致を縮退した。`test_py2cs_smoke.py`（34件）通過のうえ `check_cs_single_source_selfhost_compile.py` で `CS1503` を `58 -> 46`、`CS1502` を `45 -> 33`、`CS0266` を `34 -> 33` に縮退させた。
- `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7` `py2cs.py` の `load_east()` fallback を型付き `dict[str, Any]`（`empty_doc`）へ固定し、自己変換生成物の conditional 式型崩れを抑制した。`test_py2cs_smoke.py`（34件）通過のうえ `check_cs_single_source_selfhost_compile.py` で `CS0173` を `5 -> 4` に縮退させた。
- `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7` `prepare_selfhost_source_cs.py` の parser stub で `_` 変数再利用を撤去し、`Path`/`str` 型衝突を `*_ignored_*` へ分離した。`test_py2cs_smoke.py`（34件）通過のうえ `check_cs_single_source_selfhost_compile.py` で `CS0029` を `18 -> 17` に縮退させた。
- `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7` `prepare_selfhost_source_cs.py` の support block で `write_text_file()` を `Path.write_text()` へ差し替え、`open(...)/PyFile` 経路を撤去した。`test_py2cs_smoke.py`（34件）通過のうえ `check_cs_single_source_selfhost_compile.py` で `CS0246`/`CS0841` を 0 件化した。
- `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7` `prepare_selfhost_source_cs.py` の support block で `module_east_raw` 取得を型付き分岐へ差し替え、`dict_any_get_dict(...)` の型不一致経路を撤去した。`test_py2cs_smoke.py`（34件）通過のうえ `check_cs_single_source_selfhost_compile.py` で `CS1502` を `33 -> 32`、`CS1503` を `46 -> 45` に縮退させた。
- `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7` `prepare_selfhost_source_cs.py` の support block で `resolve_module_name` の `dict[str, str]` 参照を型付きキー参照へ差し替え、`dict_any_get_str(...)` の型不一致経路を撤去した。`test_py2cs_smoke.py`（34件）通過のうえ `check_cs_single_source_selfhost_compile.py` で `CS1502` を `32 -> 29`、`CS1503` を `45 -> 42` に縮退させた。
- `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7` `prepare_selfhost_source_cs.py` の support block で import graph 解析ループの `resolved: dict[str, str]` 読み取りを `dict_str_get(...)` へ置換し、`dict_any_get_str(...)` 由来の型不一致を縮退した。`test_py2cs_smoke.py`（34件）通過のうえ `check_cs_single_source_selfhost_compile.py` で `CS1502` を `29 -> 26`、`CS1503` を `42 -> 39` に縮退させた。
- `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7` `prepare_selfhost_source.py` の selfhost hook stub（`_call_hook`）を `return None` のみに簡素化し、C# 生成物の型衝突を削減した。`test_py2cs_smoke.py`（34件）通過のうえ `check_cs_single_source_selfhost_compile.py` で `CS0266` を `33 -> 27`、`CS0029` を `17 -> 16` に縮退させた（`CS1502=26` / `CS1503=39` は維持）。
- `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7` `prepare_selfhost_source_cs.py` で `CodeEmitter.load_profile_with_includes()` の `includes_raw` 経路を selfhost 向けに簡素化し、`object -> List<string>` 変換を回避した。`test_py2cs_smoke.py`（34件）通過のうえ `check_cs_single_source_selfhost_compile.py` で `CS1502` を `26 -> 25`、`CS1503` を `39 -> 38`、`CS0266` を `27 -> 26` に縮退させた。
