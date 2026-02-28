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

### P0: C++ 同型 cast 除去と型推論前倒し（最優先）

文脈: [docs/ja/plans/p0-cpp-redundant-same-type-cast-elimination.md](../plans/p0-cpp-redundant-same-type-cast-elimination.md)

1. [x] [ID: P0-CPP-SAMECAST-01] C++ backend の cast 規約を「同型なら無変換」に統一し、型既知経路で不要な `str(...)` / `py_to_*` を出力しないようにする。
2. [x] [ID: P0-CPP-SAMECAST-01-S1-01] 同型 cast 除去規約（source/target が同型かつ非 Any/object/unknown の場合は無変換）を C++ emitter 共通方針として固定する。
3. [x] [ID: P0-CPP-SAMECAST-01-S1-02] `get_expr_type()` の `Subscript` 推論を拡張し、`Subscript(str, int) -> str` を確定できるようにする。
4. [x] [ID: P0-CPP-SAMECAST-01-S1-03] `StrCharClassOp` を含む文字列系 lowering を修正し、型既知 `str` では `str(...)` を挿入しない。
5. [x] [ID: P0-CPP-SAMECAST-01-S2-01] `apply_cast` / `Unbox` / builtin runtime 変換経路に同型 no-op 判定を導入し、`py_to_*` の冗長連鎖を抑止する。
6. [x] [ID: P0-CPP-SAMECAST-01-S2-02] 同型 cast 非出力の回帰テスト（fixture + `sample/18` 断片検証）を追加する。
7. [x] [ID: P0-CPP-SAMECAST-01-S3-01] `sample/cpp` を再生成し、`sample/18` の compile/run/parity を再確認して結果を固定する。
- `P0-CPP-SAMECAST-01-S1-02` `CppEmitter.get_expr_type()` で `Subscript(str, int) -> str` を推論するようにし、文字列添字の型落ちを抑止した。
- `P0-CPP-SAMECAST-01-S1-03` `StrCharClassOp` で型既知 `str` は直接 `receiver.isdigit()/isalpha()` を出力し、unknown/object 経路のみ `str(...)` を維持した。
- `P0-CPP-SAMECAST-01-S2-01` `apply_cast` と `_render_unbox_target_cast` に同型 no-op 判定を追加し、推論可能な同型 cast を省略するようにした。
- `P0-CPP-SAMECAST-01-S2-02` `test_py2cpp_codegen_issues.py` に `sample/18` 回帰（`test_sample18_charclass_avoids_redundant_str_cast`）を追加し、`test_east3_cpp_bridge.py` の期待値を型既知 no-cast へ更新した。

### P0: Lua backend 追加（最優先）

文脈: [docs/ja/plans/p0-lua-backend-rollout.md](../plans/p0-lua-backend-rollout.md)

1. [x] [ID: P0-LUA-BACKEND-01] `py2lua.py` を入口として EAST3 から Lua native 直生成経路を追加し、`sample/py` の主要ケースを Lua 実行可能にする。
2. [x] [ID: P0-LUA-BACKEND-01-S1-01] Lua backend の契約（入力 EAST3、fail-closed、runtime 境界、非対象）を `docs/ja/spec` に文書化する。
3. [x] [ID: P0-LUA-BACKEND-01-S1-02] `src/py2lua.py` と `src/hooks/lua/emitter/` の骨格を追加し、最小 fixture（`add` / `if_else` / `for_range`）を通す。
4. [x] [ID: P0-LUA-BACKEND-01-S2-01] 式/文の基本 lower（代入、分岐、ループ、呼び出し、組み込み最小）を実装する。
5. [x] [ID: P0-LUA-BACKEND-01-S2-02] class/instance/isinstance/import（`math`・画像runtime含む）対応を段階実装する。
6. [x] [ID: P0-LUA-BACKEND-01-S3-01] `tools/check_py2lua_transpile.py` と `test_py2lua_smoke.py`、`runtime_parity_check --targets lua` 導線を追加し回帰を固定する。
7. [x] [ID: P0-LUA-BACKEND-01-S3-02] `sample/lua` 再生成と `docs/ja` 利用手順・対応表の同期を行う。
- `P0-LUA-BACKEND-01-S1-01` `docs/ja/spec/spec-lua-native-backend.md` を追加し、EAST3 only / fail-closed / runtime 境界 / 非対象を契約として明文化した。
- `P0-LUA-BACKEND-01-S1-02` `src/py2lua.py` と `src/hooks/lua/emitter/` の骨格を追加し、`test_py2lua_smoke.py` で `add/if_else/for_range` を通る最小 native 経路を固定した。
- `P0-LUA-BACKEND-01-S2-01` 基本 lower（`Assign/While/Dict/Subscript/IfExp/JoinedStr/Attribute` など）を追加し、`test_py2lua_smoke.py` を 12 件へ拡張。fixture 横断で `ok 22 -> 57` に改善した。
- `P0-LUA-BACKEND-01-S2-02` class/instance/isinstance/import（`math`・画像stub）を追加し、`test_py2lua_smoke.py` を 15 件へ拡張。fixture 横断で `ok 57 -> 81` に改善した。
- `P0-LUA-BACKEND-01-S3-01` `check_py2lua_transpile.py` を追加し `checked=86 ok=86 fail=0 skipped=53` を確認。`runtime_parity_check --targets lua` 導線を追加し、toolchain未導入環境でも PASS まで確認した。
- `P0-LUA-BACKEND-01-S3-02` `sample/lua` を `02/03/04/17` で再生成（`summary: total=4 skip=0 regen=4 fail=0`）し、`docs/ja/how-to-use.md` / `docs/ja/spec/spec-user.md` / `docs/ja/spec/spec-import.md` / `sample/readme-ja.md` を Lua 導線に同期した。

### P1: Go/Java/Swift/Ruby runtime 外出し（inline helper 撤去）

文脈: [docs/ja/plans/p1-runtime-externalization-gjsr.md](../plans/p1-runtime-externalization-gjsr.md)

1. [ ] [ID: P1-RUNTIME-EXT-01] Go/Java/Swift/Ruby の生成コードから `__pytra_*` runtime helper の inline 定義を撤去し、言語別 runtime ファイル参照へ統一する。
2. [x] [ID: P1-RUNTIME-EXT-01-S1-01] 現行 emitter が inline 出力している helper 群を言語別に棚卸しし、runtime 側 API（正本）との対応表を固定する。
3. [x] [ID: P1-RUNTIME-EXT-01-S2-01] Go backend を runtime 外部参照方式へ移行し、`py2go` 出力から helper 本体を除去する。
4. [x] [ID: P1-RUNTIME-EXT-01-S2-02] Java backend を runtime 外部参照方式へ移行し、`py2java` 出力から helper 本体を除去する。
5. [x] [ID: P1-RUNTIME-EXT-01-S2-03] Swift backend 用の native runtime ファイルを整備し、`py2swift` 出力から helper 本体を除去する。
6. [ ] [ID: P1-RUNTIME-EXT-01-S2-04] Ruby backend 用 runtime ファイルを新設し、`py2rb` 出力から helper 本体を除去する。
7. [ ] [ID: P1-RUNTIME-EXT-01-S3-01] `runtime_parity_check` / smoke テスト / sample 再生成導線を runtime 外部参照前提に更新し、回帰を固定する。
- `P1-RUNTIME-EXT-01-S1-01` Go/Java/Swift/Ruby の inline helper 群と runtime 正本 API の対応表を `docs/ja/plans/p1-runtime-externalization-gjsr.md` に固定し、Go/Java は命名差吸収、Swift/Ruby は runtime 正本新設が主要ギャップと整理した。
- `P1-RUNTIME-EXT-01-S2-01` Go native emitter から `func __pytra_*` inline 定義を撤去し、`py2go.py` で `py_runtime.go` を出力先へ配置する導線へ移行した。`test_py2go_smoke.py` と `runtime_parity_check --targets go`（`sample/18`）で実行導線を確認した。
- `P1-RUNTIME-EXT-01-S2-02` Java native emitter から helper 本体定義を撤去し、呼び出しを `PyRuntime.__pytra_*` へ集約した。`py2java.py` で `PyRuntime.java` を出力先へ配置し、`test_py2java_smoke.py` と `runtime_parity_check --targets java`（`sample/18`）で実行導線を確認した。
- `P1-RUNTIME-EXT-01-S2-03` Swift native emitter から helper 本体定義を撤去し、`src/runtime/swift/pytra/py_runtime.swift` へ移管した。`py2swift.py` で `py_runtime.swift` を出力先へ配置し、`test_py2swift_smoke.py` を通過。`runtime_parity_check --targets swift` は `swiftc` 未導入環境のため `toolchain_missing` を確認した。

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
