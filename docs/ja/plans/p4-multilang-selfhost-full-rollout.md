# P4: 全言語 selfhost 完全化（低低優先）

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P4-MULTILANG-SH-01`

背景:
- 現状の multilang selfhost 状態では、C++ 以外に `stage1/stage2/stage3` の未達が残っている。
- `rs` は stage1 失敗、`cs`/`js` は stage2 失敗、`ts` は preview-only、`go/java/swift/kotlin` は multistage runner 未定義。
- 将来的に「全言語で自己変換チェーンが成立する」状態を作るため、低低優先で長期バックログ化する。

目的:
- `py2<lang>.py`（`cpp/rs/cs/js/ts/go/java/swift/kotlin`）の selfhost 成立条件を段階的に満たし、全言語で multistage 監視を通せる状態へ収束する。

対象:
- `tools/check_multilang_selfhost_stage1.py` / `tools/check_multilang_selfhost_multistage.py` / `tools/check_multilang_selfhost_suite.py`
- 各言語の `py2*.py` と対応 emitter/runtime
- selfhost 検証レポート（`docs/ja/plans/p1-multilang-selfhost-*.md`）の更新導線

非対象:
- 速度最適化やコードサイズ最適化
- backend 全面再設計（selfhost 成立に不要な大規模改修）
- 優先度 `P0` / `P1` / `P3` の既存タスクを追い越す着手

受け入れ基準:
- `tools/check_multilang_selfhost_suite.py` 実行結果で全言語が `stage1 pass` となる。
- multistage レポートで全言語が `stage2 pass` / `stage3 pass`（または明示的な恒久除外）になる。
- `runner_not_defined` / `preview_only` / `toolchain_missing` 依存の常態化が解消される。

確認コマンド:
- `python3 tools/check_multilang_selfhost_suite.py`
- `python3 tools/check_multilang_selfhost_stage1.py`
- `python3 tools/check_multilang_selfhost_multistage.py`
- `python3 tools/build_selfhost.py`

決定ログ:
- 2026-02-27: ユーザー要望により、全言語 selfhost 完全化を低低優先（P4）で TODO 追加する方針を確定した。
- 2026-02-27: [ID: `P4-MULTILANG-SH-01-S1-01`] `python3 tools/check_multilang_selfhost_suite.py` を再実行し、`docs/ja/plans/p1-multilang-selfhost-status.md` / `docs/ja/plans/p1-multilang-selfhost-multistage-status.md` を更新した。未達カテゴリを言語別に固定し、blocking chain を確定した。
- 2026-02-27: [ID: `P4-MULTILANG-SH-01-S1-02`] `runner_not_defined` 対象（go/java/swift/kotlin）の multistage runner 契約を定義し、`check_multilang_selfhost_multistage.py` へ段階実装する API 形を確定した。
- 2026-02-27: [ID: `P4-MULTILANG-SH-01-S2-01`] `src/py2rs.py` の括弧付き `from-import` を selfhost parser 互換の単一行 import へ修正し、`python3 tools/check_multilang_selfhost_stage1.py` / `python3 tools/check_multilang_selfhost_multistage.py` で `rs stage1=pass` を確認した。`rs` の先頭失敗は `stage1_transpile_fail` から `compile_fail`（stage2 build）へ遷移した。
- 2026-02-27: [ID: `P4-MULTILANG-SH-01-S2-02-S1`] C# emitter の selfhost compile 阻害を一段解消（`Path` alias/constructor, `str.endswith|startswith` 変換, 関数定義の定数デフォルト引数出力）。`check_multilang_selfhost_*` 再実行で `cs` の先頭失敗が `Path` 未解決から `sys` 未解決へ遷移し、次ブロッカーを特定した。
- 2026-02-27: [ID: `P4-MULTILANG-SH-01-S2-02-S2-S1`] C# emitter で `sys.exit` を `System.Environment.Exit` へ lower し、文字列 docstring 式の不要出力を抑止した。`check_multilang_selfhost_*` 再実行で `cs` の先頭失敗が `sys` 未解決から `transpile_to_csharp` 未解決へ遷移し、import 依存閉包（単体 selfhost source 生成 or モジュール連結）の実装が次ブロッカーと確定した。
- 2026-02-27: [ID: `P4-MULTILANG-SH-01-S2-02-S2-S2-S1`] 単体 selfhost source 方式の PoC として `tools/prepare_selfhost_source_cs.py` を追加し `selfhost/py2cs.py` を生成。`python3 src/py2cs.py selfhost/py2cs.py -o /tmp/cs_selfhost_full_stage1.cs` を検証した結果、`unsupported_syntax: object receiver attribute/method access is forbidden by language constraints`（`selfhost/py2cs.py` 変換中）で停止し、現行 C# 制約下では PoC が未通過であることを確認した。
- 2026-02-27: [ID: `P4-MULTILANG-SH-01-S2-02-S2-S2-S1`] `prepare_selfhost_source_cs.py` に C++ selfhost 同等の hook 無効化パッチ（`_call_hook` stub 化 + `set_dynamic_hooks_enabled(False)`）を追加して再検証したが、`selfhost/py2cs.py` の `CSharpEmitter._walk_node_names` 内 `node.get(...)` で同系統の制約違反が継続（`object receiver attribute/method access`）。PoC の阻害要因は dynamic hook 以外にも存在すると確定した。
- 2026-02-27: [ID: `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S1`] `CSharpEmitter._walk_node_names` の `Any` 直アクセス（`node.get` / `node.items`）を helper 経由へ置換し、`prepare_selfhost_source_cs.py` 再生成後の `python3 src/py2cs.py selfhost/py2cs.py -o /tmp/cs_selfhost_full_stage1.cs` が成功することを確認した。単体 selfhost source PoC の阻害要因は parse 制約から compile 失敗（`default literal` / C++風テンプレート断片混入等）へ遷移した。
- 2026-02-27: [ID: `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S1`] `tools/check_cs_single_source_selfhost_compile.py` を追加し、単体 selfhost source compile 失敗の定期分類レポート `docs/ja/plans/p4-cs-single-source-selfhost-compile-status.md` を生成した。`mcs -langversion:latest` 条件で `CS1525=175` / `CS1002=21` / `CS1519=6` / `CS1520=3` / `CS0136=2` を固定し、主因を「テンプレート断片混入」と「呼び出し形状崩れ」に分類した。
- 2026-02-27: [ID: `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S2`] C# emitter の compile 失敗要因に対し、`JoinedStr` lower（C# 補間文字列）/`Set` lower（`HashSet<object>`）/optional 引数の suffix 制約順守/ローカル変数 shadow 回避を実装。`python3 test/unit/test_py2cs_smoke.py`（26件）と `python3 tools/check_cs_single_source_selfhost_compile.py` を再実行し、`CS1525/CS1002` を 0 件化した。現状の先頭阻害は `mcs` 内部例外 `NotImplementedException: tuples > 7` に収束した。
- 2026-02-27: [ID: `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S3`] tuple arity が `1` または `>7` のときに `List<object>` へ lower する C# emitter 修正（型/式/tuple unpack 参照）を実装し、`python3 test/unit/test_py2cs_smoke.py`（28件）を通過。`python3 tools/check_cs_single_source_selfhost_compile.py` で `mcs` 内部例外 `NotImplementedException: tuples > 7` が消失し、失敗モードが通常 compile エラー（`CS1061/CS0103/CS1503` 主体）へ遷移した。
- 2026-02-27: [ID: `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S4`] C# class 出力で base 句（`class Child : Base`）を維持する修正を追加し、自己変換生成物で継承チェーンが復元されるようにした。`python3 tools/check_cs_single_source_selfhost_compile.py` の再計測で `CS1061` は `469 -> 109` に縮退し、失敗件数上位の先頭カテゴリを削減できた。
- 2026-02-27: [ID: `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S5`] `set/list/dict` の lower を型ヒント連動で補強し、`for ch in str` を `ToString()` 投影に変換、`strip/find/rfind/replace` lower を追加した。`python3 test/unit/test_py2cs_smoke.py`（32件）を通過し、`python3 tools/check_cs_single_source_selfhost_compile.py` で `CS1061` は `109 -> 20`、`CS0103` は `81 -> 36` へ縮退した。
- 2026-02-27: [ID: `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S6`] `@staticmethod/@classmethod` の static 出力を実装し、`json.loads` lower と `dict.get/items` の unknown 型フォールバックを追加した。`python3 test/unit/test_py2cs_smoke.py`（32件）を通過し、`python3 tools/check_cs_single_source_selfhost_compile.py` で `CS0120` は `5 -> 0`、`CS1061` は `20 -> 10`、`CS0103` は `36 -> 34` に縮退した。
- 2026-02-27: [ID: `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7`] `CSharpEmitter._collect_using_lines` のローカル helper をクラスメソッドへ抽出し、`_emit_assign` の `item_expr` を事前初期化した。`python3 test/unit/test_py2cs_smoke.py`（34件）を通過し、`python3 tools/check_cs_single_source_selfhost_compile.py` で `CS0103` を `34 -> 12` へ縮退させた（`CS1503/CS0266` は継続課題）。
- 2026-02-27: [ID: `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7`] C# selfhost compile 向けに keyword 引数呼び出し崩れ対策（`code_emitter`/`cs_emitter`/`transpile_cli`）、`chr/ord` lower、`py2cs.py` の argparse 依存除去、`prepare_selfhost_source(_cs).py` の補助生成を実施した。`python3 test/unit/test_py2cs_smoke.py`（34件）は継続通過し、`python3 tools/check_cs_single_source_selfhost_compile.py` で `CS0103` を `12 -> 1`、`CS0815` を `5 -> 3` まで縮退させた（主残件は `CS1502/CS1503/CS0266` の型不一致群）。
- 2026-02-28: [ID: `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7`] `tools/prepare_selfhost_source_cs.py` の `__main__` ガード置換を `main([str(x) for x in args])` へ更新し、selfhost C# 入口の `sys.argv` 依存を撤去した。`python3 tools/check_cs_single_source_selfhost_compile.py` の再計測で `CS0103` を `1 -> 0`、`CS1503` を `61 -> 60`、`CS1502` を `47 -> 46` へ縮退させ、先頭 compile note を `string[] -> List<string>` から `Dictionary<string,string> -> Dictionary<string,object>` へ前進させた。
- 2026-02-28: [ID: `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7`] `src/pytra/compiler/east_parts/code_emitter.py` の `EmitterHooks.to_dict` を `out[str(key)]` 化し、`_root_scope_stack` の返却を `set[str]` 明示ローカルへ変更した。`python3 -m unittest discover -s test/unit -p 'test_py2cs_smoke.py' -v`（34件）を通過し、`python3 tools/check_cs_single_source_selfhost_compile.py` の再計測で `CS1503` を `60 -> 58`、`CS1502` を `46 -> 45`、`CS1950` を `14 -> 13` に縮退させた（`CS0266=34` は継続）。
- 2026-02-28: [ID: `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7`] `src/py2cs.py` の `_arg_get_str` シグネチャを `dict[str, str]` へ整合させ、selfhost 生成物での `Dictionary<string,string>` / `Dictionary<string,object>` 混在による型不一致を縮退した。`python3 -m unittest discover -s test/unit -p 'test_py2cs_smoke.py' -v`（34件）を通過し、`python3 tools/check_cs_single_source_selfhost_compile.py` で `CS1503` を `58 -> 46`、`CS1502` を `45 -> 33`、`CS0266` を `34 -> 33` まで縮退させた（`CS0103=0` 維持）。
- 2026-02-28: [ID: `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7`] `src/py2cs.py` の `load_east()` で fallback 辞書を `dict[str, Any]` 明示（`empty_doc`）へ固定し、自己変換生成物の conditional 式型崩れを抑止した。`python3 -m unittest discover -s test/unit -p 'test_py2cs_smoke.py' -v`（34件）を再通過し、`python3 tools/check_cs_single_source_selfhost_compile.py` で `CS0173` を `5 -> 4` に縮退させた（`CS1502=33` / `CS1503=46` / `CS0266=33` は維持）。
- 2026-02-28: [ID: `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7`] `tools/prepare_selfhost_source_cs.py` の parser stub で `_` 変数再利用を撤去し、`Path` / `str` の型衝突を回避するよう `*_ignored_*` 変数へ分離した。`python3 -m unittest discover -s test/unit -p 'test_py2cs_smoke.py' -v`（34件）を通過し、`python3 tools/check_cs_single_source_selfhost_compile.py` の再計測で `CS0029` を `18 -> 17` に縮退、先頭 compile note を `string -> py_path` から `CS0841` へ前進させた。
- 2026-02-28: [ID: `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7`] `tools/prepare_selfhost_source_cs.py` で selfhost 用 support block の `write_text_file()` を `open(...)/PyFile` 経路から `Path.write_text()` へ差し替えた。`python3 -m unittest discover -s test/unit -p 'test_py2cs_smoke.py' -v`（34件）を通過し、`python3 tools/check_cs_single_source_selfhost_compile.py` で `CS0246` と `CS0841` を 0 件化、先頭 compile note を `Dictionary<string,Dictionary<string,object>> -> Dictionary<string,object>` の `CS1503` へ前進させた。
- 2026-02-28: [ID: `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7`] `tools/prepare_selfhost_source_cs.py` の support block パッチを拡張し、`build_module_east_map_from_analysis` の `module_east_raw` 取得を `dict_any_get_dict(...)` から型付き分岐（`if key in module_east_raw: east = module_east_raw[key]`）へ差し替えた。`python3 -m unittest discover -s test/unit -p 'test_py2cs_smoke.py' -v`（34件）を通過し、`python3 tools/check_cs_single_source_selfhost_compile.py` で `CS1502` を `33 -> 32`、`CS1503` を `46 -> 45` に縮退させた。
- 2026-02-28: [ID: `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7`] `tools/prepare_selfhost_source_cs.py` の support block パッチを拡張し、`resolve_module_name` 内の `resolved: dict[str, str]` 参照を `dict_any_get_str(...)` から型付きキー参照へ差し替えた。`python3 -m unittest discover -s test/unit -p 'test_py2cs_smoke.py' -v`（34件）を通過し、`python3 tools/check_cs_single_source_selfhost_compile.py` で `CS1502` を `32 -> 29`、`CS1503` を `45 -> 42` に縮退、先頭 compile note を `CS1579` へ前進させた。
- 2026-02-28: [ID: `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7`] `tools/prepare_selfhost_source_cs.py` の support block パッチを拡張し、import graph 構築ループで `resolved: dict[str, str]` を読む 3 箇所（`status/path/module_id`）を `dict_any_get_str(...)` から `dict_str_get(...)` へ置換した。`python3 -m unittest discover -s test/unit -p 'test_py2cs_smoke.py' -v`（34件）を通過し、`python3 tools/check_cs_single_source_selfhost_compile.py` で `CS1502` を `29 -> 26`、`CS1503` を `42 -> 39` に縮退させた（`CS1579=6` 維持）。
- 2026-02-28: [ID: `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7`] `tools/prepare_selfhost_source.py` の selfhost hook stub（`_call_hook`）から引数ダミー代入を撤去し、`return None` のみへ簡素化した。`python3 -m unittest discover -s test/unit -p 'test_py2cs_smoke.py' -v`（34件）と `python3 tools/check_cs_single_source_selfhost_compile.py` を再実行し、`CS0266` を `33 -> 27`、`CS0029` を `17 -> 16` に縮退させた（`CS1502=26` / `CS1503=39` は維持）。
- 2026-02-28: [ID: `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7`] `tools/prepare_selfhost_source_cs.py` で `CodeEmitter.load_profile_with_includes()` の `includes_raw` 経路を selfhost 向けに簡素化し、`object -> List<string>` 変換を避けた。`python3 -m unittest discover -s test/unit -p 'test_py2cs_smoke.py' -v`（34件）と `python3 tools/check_cs_single_source_selfhost_compile.py` を再実行し、`CS1502` を `26 -> 25`、`CS1503` を `39 -> 38`、`CS0266` を `27 -> 26` に縮退させた。
- 2026-03-01: [ID: `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7`] C# emitter の `Try` lower を拡張し、複数 `except` ハンドラを `catch(System.Exception ex)` + 分岐へ変換可能にした。`python3 -m unittest discover -s test/unit -p 'test_py2cs_smoke.py' -v`（36件）を通過し、`python3 tools/check_cs_single_source_selfhost_compile.py` で selfhost の失敗モードを `transpile fail` から `compile fail` に前進させた（`transpile rc=0`, 先頭 note は `CS1579`）。
- 2026-03-01: [ID: `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7`] C# emitter の `for-in` で `object/unknown` 反復対象を `System.Collections.IEnumerable` へ明示キャストする補正を追加し、`foreach on object`（`CS1579`）を解消した。`python3 -m unittest discover -s test/unit -p 'test_py2cs_smoke.py' -v`（37件）通過のうえ、`python3 tools/check_cs_single_source_selfhost_compile.py` の上位エラーを `CS1061/CS1503/CS0266` 主体へ更新した。
- 2026-03-01: [ID: `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7`] `dict.items()` 反復時は `IEnumerable` キャストを抑止して `KeyValuePair` 形を維持する補正を追加し、`object.Key/object.Value` 起因の `CS1061/CS0131` 群を解消した。`python3 -m unittest discover -s test/unit -p 'test_py2cs_smoke.py' -v`（38件）を通過し、`python3 tools/check_cs_single_source_selfhost_compile.py` の先頭失敗は `CS1503`（`object -> string`）へ遷移した。
- 2026-03-01: [ID: `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7`] `CodeEmitter.require_dep_any()` の string 化経路を明示し、selfhost C# 生成物の `require_dep(object)` 呼び出し由来 `CS1502/CS1503` を縮退した。
- 2026-03-01: [ID: `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7`] C# emitter に `sorted()` lower（`OrderBy(...).ToList()`）を追加し、selfhost compile の先頭エラーを `sorted` 未解決から次段（`string * long`）へ前進させた。`test_py2cs_smoke.py` は 39 件で通過。
- 2026-03-01: [ID: `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7`] C# emitter に文字列乗算（`\"...\" * n`）lower を追加し、selfhost compile の `CS0019 string * long` を先頭ブロッカーから除去した。`test_py2cs_smoke.py` は 40 件で通過し、先頭エラーは `CS0266 object -> bool` へ遷移した。
- 2026-03-01: [ID: `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7`] `CodeEmitter` の hook 真偽判定を `any_to_bool(...)` 経由へ統一し、selfhost C# 生成物で `object` を直接 bool 評価していた経路を縮退した。`test_code_emitter.py`（47件）/`test_py2cs_smoke.py`（40件）通過のうえ、compile 先頭エラーは `CS0266` から `CS0029 (Dictionary<string,object> -> string)` へ遷移した。
- 2026-03-01: [ID: `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7`] `CodeEmitter` の hook 戻り値型正規化（`str/bool`）、ASCII 判定 helper 化、`any_to_dict/any_to_list/_dict_stmt_list` の object 直返し撤去、`declare_in_current_scope` の `set[str]` 初期化を実装した。`PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_code_emitter.py' -v`（47件）と `... -p 'test_py2cs_smoke.py' -v`（40件）を通過し、`python3 tools/check_cs_single_source_selfhost_compile.py` 再計測で `CS0266: 25 -> 9`, `CS0019: 18 -> 11`, `CS0029: 18 -> 17`, `CS1502: 29 -> 27`, `CS1503: 42 -> 40` へ縮退させた（先頭は `CS1503 object -> string`）。
- 2026-03-01: [ID: `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7`] `fallback_tuple_target_names_from_repr` の ASCII 判定を共通 helper に寄せ、`any_to_dict/any_to_dict_or_empty` の複製経路と `pseudo_target: dict[str, Any]` 型注釈を調整して C# selfhost compile の型崩れを追加縮退した。`PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_code_emitter.py' -v`（47件）/`... -p 'test_py2cs_smoke.py' -v`（40件）通過のうえ、`python3 tools/check_cs_single_source_selfhost_compile.py` で `CS1502: 27 -> 26`, `CS1503: 40 -> 39` を確認した（先頭は継続して `CS1503 object -> string`）。
- 2026-03-01: [ID: `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7`] C# emitter に `Program.PytraDictStringObjectFromAny(object)` helper を追加し、`dict(...)`（typed hint 含む）を object-safe 変換経路へ切替えた。helper 出力タイミングを `Main` 生成後へ移し、`test_py2cs_smoke.py` に dict-helper 回帰（41件）を追加。`python3 tools/check_cs_single_source_selfhost_compile.py` 再計測で `CS1502: 26 -> 24`, `CS1503: 39 -> 37` まで縮退した。
- 2026-03-01: [ID: `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7`] C# emitter の代入出力で `var x = null;` を `object x = null;` へ切替え、selfhost compile で発生していた `CS0815`（null 初期化 var）を解消した。`PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cs_smoke.py' -v`（41件）を通過し、`python3 tools/check_cs_single_source_selfhost_compile.py` で `CS0815/CS0411` が 0 件であることを確認した。
- 2026-03-01: [ID: `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7`] C# emitter の dict literal 型推論に fail-closed widening を追加し、値が混在/unknown を含む場合は `Dictionary<string, object>` へ自動拡張するよう補正した。`test_py2cs_smoke.py` に回帰（42件）を追加して通過し、`python3 tools/check_cs_single_source_selfhost_compile.py` で `CS1503: 37 -> 22`, `CS1502: 24 -> 22`, `CS0029: 17 -> 16` まで縮退させた。
- 2026-03-01: [ID: `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7`] `CodeEmitter.any_dict_get*` の受け口を `Any` 化し、実装本体を `any_to_dict_or_empty()` 経由へ統一して object 直接メンバアクセスを排除した。`test_code_emitter.py`（47件）/`test_py2cs_smoke.py`（42件）を通過し、`python3 tools/check_cs_single_source_selfhost_compile.py` で `CS1503: 22 -> 18`, `CS1502: 22 -> 18` まで縮退させた（`CS1929/CS0021` は各1件で維持）。
- 2026-03-01: [ID: `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7`] `_emit_annassign` の `Attribute` 経路でも型ヒントを使って `_render_expr_with_type_hint` を適用するよう補強し、`self.x: set[str] = ...` / `self.y: dict[str, str] = ...` の初期化を typed 出力へ揃えた。`test_py2cs_smoke.py` に回帰（43件）を追加して通過し、`python3 tools/check_cs_single_source_selfhost_compile.py` で `CS0029: 16 -> 10` を確認した（`CS1502/CS1503=18` 維持）。

## 現状固定（S1-01）

言語別未達要因（2026-02-27）:

| lang | stage1 | stage2 | stage3 | category | 先頭原因 |
| --- | --- | --- | --- | --- | --- |
| rs | fail | skip | skip | `stage1_transpile_fail` | `unsupported from-import clause` |
| cs | pass | fail | skip | `compile_fail` | `Path` 型未解決（`System.IO` 参照不足） |
| js | pass | fail | skip | `stage1_dependency_transpile_fail` | JS emitter の `object receiver attribute/method access` 制約違反 |
| ts | pass | blocked | blocked | `preview_only` | 生成 transpiler が preview-only |
| go | pass | skip | skip | `runner_not_defined` | multistage runner 未定義 |
| java | pass | skip | skip | `runner_not_defined` | multistage runner 未定義 |
| swift | pass | skip | skip | `runner_not_defined` | multistage runner 未定義 |
| kotlin | pass | skip | skip | `runner_not_defined` | multistage runner 未定義 |

優先順（blocking chain）:
1. `rs` の stage1 失敗を解消（以降の stage2/stage3 検証が不可）。
2. `cs` の stage2 compile 失敗を解消（stage3 へ進めない）。
3. `js` の stage2 依存 transpile 失敗を解消（stage3 へ進めない）。
4. `ts` の preview-only を解消（stage2/stage3 の評価自体が blocked）。
5. `go/java/swift/kotlin` の runner 契約を定義し、`runner_not_defined` を解消して multistage 監視対象へ昇格。

## Runner 契約（S1-02）

目的:
- `check_multilang_selfhost_multistage.py` の `runner_not_defined` を、言語別 adapter 実装で段階的に置換する。

共通 API 契約（実装方針）:
1. `build_stage1(lang, stage1_src, stage1_runner)`:
   - stage1 生成 transpiler ソース（`stage1_src`）を実行可能 runner（binary/jar）へ変換する。
2. `run_stage2(lang, stage1_runner, src_py, stage2_src)`:
   - stage1 runner で `src/py2<lang>.py` を再変換し、`stage2_src` を生成する。
3. `build_stage2(lang, stage2_src, stage2_runner)`:
   - stage2 transpiler ソースを実行可能 runner へ変換する。
4. `run_stage3(lang, stage2_runner, sample_py, stage3_out)`:
   - stage2 runner で `sample/py/01_mandelbrot.py` を変換し、`stage3_out` 生成有無で pass/fail 判定する。

言語別 runner 契約:

| lang | build_stage1 / build_stage2 | run_stage2 / run_stage3 | 成功条件 |
| --- | --- | --- | --- |
| go | `go build -o <runner> <stage*.go>` | `<runner> <input.py> -o <out.go>` | `out.go` が生成される |
| java | `javac <stage*.java>`（main class は stage 出力規約で固定） | `java -cp <dir> <main_class> <input.py> -o <out.java>` | `out.java` が生成される |
| swift | `swiftc <stage*.swift> -o <runner>` | `<runner> <input.py> -o <out.swift>` | `out.swift` が生成される |
| kotlin | `kotlinc <stage*.kt> -include-runtime -d <runner.jar>` | `java -jar <runner.jar> <input.py> -o <out.kt>` | `out.kt` が生成される |

実装時の fail 分類ルール:
- build 失敗: `compile_fail` / `stage2_compile_fail`
- 実行失敗: `self_retranspile_fail` / `sample_transpile_fail`
- 生成物欠落: 実行失敗カテゴリへ含め、`output missing` を note に付与

## 分解

- [x] [ID: P4-MULTILANG-SH-01-S1-01] 現状の stage1/stage2/stage3 未達要因を言語別に固定化し、優先順（blocking chain）を明文化する。
- [x] [ID: P4-MULTILANG-SH-01-S1-02] multistage runner 未定義言語（go/java/swift/kotlin）の runner 契約を定義し、`runner_not_defined` を解消する実装方針を確定する。
- [x] [ID: P4-MULTILANG-SH-01-S2-01] Rust selfhost の stage1 失敗（from-import 受理）を解消し、stage2 へ進める。
- [ ] [ID: P4-MULTILANG-SH-01-S2-02] C# selfhost の stage2 compile 失敗を解消し、stage3 変換を通す。
- [x] [ID: P4-MULTILANG-SH-01-S2-02-S1] C# emitter の selfhost 互換ギャップ（`Path`/`str.endswith|startswith`/定数デフォルト引数）を埋め、先頭 compile エラーを前進させる。
- [ ] [ID: P4-MULTILANG-SH-01-S2-02-S2] `py2cs.py` selfhost 生成物の import 依存解決方針（単体 selfhost source 生成 or モジュール連結）を確定し、`sys/argparse/transpile_cli` 未解決を解消する。
- [x] [ID: P4-MULTILANG-SH-01-S2-02-S2-S1] C# selfhost 先頭エラーの足切り（`sys.exit` / docstring式）を解消し、import 依存未解決の先頭シンボルを確定する。
- [ ] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2] C# selfhost 用の import 依存閉包方式（単体 selfhost source 生成 or モジュール連結）を実装し、`transpile_to_csharp` 未解決を解消する。
- [x] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2-S1] 単体 selfhost source 方式の PoC（`prepare_selfhost_source_cs.py`）を実装し、変換可否を実測で確認する。
- [ ] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2-S2] PoC 失敗要因（C# object receiver 制約）を解消するか、モジュール連結方式へ pivot して import 依存閉包を成立させる。
- [x] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S1] 単体 selfhost source PoC の parse 制約（object receiver access）を解消し、`selfhost/py2cs.py` の C# 変換を通す。
- [ ] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2] 単体 selfhost source 生成物（`cs_selfhost_full_stage1.cs`）の compile 失敗を分類し、mcs 通過に必要な emit/runtime 互換ギャップを埋める。
- [x] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S1] compile 失敗の機械分類ツールを追加し、エラーコード/カテゴリの現状値をレポート化する。
- [x] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S2] 分類結果（テンプレート断片混入 / 呼び出し形状崩れ / shadowed local）に対応する修正を実装し、`CS1525/CS1002` を段階的に削減する。
- [x] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S3] `mcs` 内部例外（`tuples > 7`）を回避する emit 方針を実装し、stage2 compile を次段検証可能な状態へ戻す。
- [x] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S4] `mcs` で顕在化した通常 compile エラー（`CS1061/CS0103/CS1503` 上位群）の先頭カテゴリを削減し、stage2 失敗件数を継続的に縮退させる。
- [x] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S5] 残存上位エラー（`CS0103 set/list/json` と `CS0019 char/string`）を対象に emitter lower を追加し、stage2 compile 失敗件数をさらに縮退させる。
- [x] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S6] 残存の主要失敗（`json` 未解決、`dict.get/items` 未lower、`CodeEmitter` static参照不整合）を段階解消し、stage2 compile の上位エラー構成を更新する。
- [ ] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7] 残存上位エラー（`_add`/`item_expr` の未定義、`object` 由来の `CS1503/CS0266`）を対象に nested helper/型縮約を補強し、stage2 compile 件数をさらに削減する。
- [ ] [ID: P4-MULTILANG-SH-01-S2-02-S3] C# selfhost の stage2/stage3 を通し、`compile_fail` から `pass` へ到達させる。
- [ ] [ID: P4-MULTILANG-SH-01-S2-03] JS selfhost の stage2 依存 transpile 失敗を解消し、multistage を通す。
- [ ] [ID: P4-MULTILANG-SH-01-S3-01] TypeScript の preview-only 状態を解消し、selfhost 実行可能な生成モードへ移行する。
- [ ] [ID: P4-MULTILANG-SH-01-S3-02] Go/Java/Swift/Kotlin の native backend 化タスクと接続し、selfhost 実行チェーンを有効化する。
- [ ] [ID: P4-MULTILANG-SH-01-S4-01] 全言語 multistage 回帰を CI 導線へ統合し、失敗カテゴリの再発を常時検知できるようにする。
- [ ] [ID: P4-MULTILANG-SH-01-S4-02] 完了判定テンプレート（各言語の stage 通過条件と除外条件）を文書化し、運用ルールを固定する。
