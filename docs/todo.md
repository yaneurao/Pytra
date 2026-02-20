# TODO（未完了のみ）

## 最優先（2026-02-20 追加: py2cpp コード生成不具合）

- [x] `py2cpp.py` の分岐内初回代入（関数スコープ変数）が C++ でブロックスコープ宣言になってしまう問題を修正する。
  - [x] 原因調査:
    - `emit_assign`（`src/py2cpp.py`）が `is_declared` 判定を現在スコープ基準で行うため、`if/else` 内初回代入が `str x = ...;` として各ブロックに閉じる。
    - その後の `return x + y` はブロック外参照となり、未宣言エラーを誘発する。
  - [x] 最小再現の生成テストを追加:
    - `test/unit/test_py2cpp_codegen_issues.py::Py2CppCodegenIssueTest::test_branch_first_assignment_is_hoisted_before_if`
    - `test/unit/test_py2cpp_codegen_issues.py::Py2CppCodegenIssueTest::test_optional_tuple_destructure_keeps_str_type`
  - [x] 修正:
    - 関数単位で「分岐後にも参照されるローカル」を事前収集し、`if/else` の外側で宣言、分岐内は代入のみを出力する。
    - `TupleAssign` で `tuple[...]|None` からの代入時に `optional` を展開してから `std::get<>` する。
    - 事前宣言変数への代入で型情報を見失わないよう `declared_var_types` のフォールバックを追加する。
  - [x] 受け入れ条件:
    - 上記 2 テストが green であること（skip なし）。: `python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py'` で `2/2 OK`。
    - `runtime/cpp/pytra/std/json.cpp` 末尾 `dumps()` と同種のスコープ崩れが再発しないことを確認する。: `--emit-runtime-cpp` 再生成 + `g++ -c src/runtime/cpp/pytra/std/json.cpp` を確認済み。

## 優先方針（2026-02-19 更新）

- まず `import` 解決（依存グラフ・探索パス・`from ... import ...` を含む）を先に完了させる。
- `selfhost` は import 解決完了後に回す（手戻り抑制のため）。

## 直近実行キュー（細分化）

1. [ ] selfhost `.py` 経路の段階回復
   - [x] `load_east` スタブ置換のために必要な EAST 変換依存（parser/east_io）を最小単位で棚卸しする。
     - 依存本体: `src/pytra/compiler/east_parts/core.py::{EastBuildError, convert_path, convert_source_to_east_with_backend}`
     - 主要 shim 依存: `pytra.std.argparse`, `pytra.std.json`, `pytra.std.re`, `pytra.std.pathlib`, `pytra.std.sys`, `pytra.std.dataclasses`, `pytra.std.typing`
     - selfhost 非対応要素: `src/pytra/compiler/east.py` facade の bootstrap path 操作（`import sys as _bootstrap_sys` と `sys.path.insert`）
   - [x] `tools/prepare_selfhost_source.py` に取り込み可能な関数群を「安全（selfhost通過済み）」と「要分割」に分ける。
     - 安全（通過済み）: `CodeEmitter` 本体、`transpile_cli` の関数群（`parse_py2cpp_argv` など）、main差し替え
     - 要分割: `src/pytra/compiler/east.py` facade 経由の import 連鎖、`east_parts.core` 全量取り込み（サイズ過大かつ selfhost 変換コスト高）
   - [ ] `sample/py/01_mandelbrot.py` を selfhost 経路で `-o` 生成できるところまで回復する。
     - [x] 暫定ブリッジ `tools/selfhost_transpile.py` を追加し、`.py -> EAST JSON -> selfhost` で `test/fixtures/core/add.py` の生成を確認。
     - [x] 同ブリッジ経路で `sample/py/01_mandelbrot.py` の `-o` 生成を確認。
     - [ ] pure selfhost（中間 Python 呼び出しなし）で `.py -> -o` を通す。
      - [ ] `selfhost/py2cpp.out` 側に `load_east(.py)` の実処理を実装し、`not_implemented` を返さないようにする。
         - [ ] `load_east(.py)` を `load_east_from_path(..., parser_backend="self_hosted")` ベースに置換する。
         - [ ] selfhost 最小モードの `load_east(.json)` を復活させ、`tools/check_selfhost_cpp_diff.py --selfhost-driver bridge` を再び通す（`std::any` 退化を回避した実装にする）。
           - [x] `.json` 読み込み自体は復活し、`bridge-json-unavailable` skip は解消した（2026-02-20）。
           - [x] `tools/check_selfhost_cpp_diff.py --selfhost-driver bridge` の既定ケースで `mismatches=0` を達成する。: `test/fixtures/core/add.py`, `test/fixtures/control/if_else.py`, `test/fixtures/collections/comprehension_filter.py`, `sample/py/01_mandelbrot.py` で `mismatches=0` を確認済み（2026-02-20）。
           - [x] 暫定措置: `check_selfhost_cpp_diff --mode allow-not-implemented --selfhost-driver bridge` では `[input_invalid]` を skip 扱いにした（本タスク完了時に戻す）。
           - [x] `src/pytra/std/json.py` を C++ へ安全に生成できるサブセットへ段階分割し、`runtime/cpp/pytra/std/json.cpp` の selfhost ビルドエラー（`ord/chr` / 文字列 `.begin()` / optional tuple 展開など）を解消する。: `json.cpp` 単体コンパイル通過、`json_extended` の Python/C++ 出力一致を確認済み（2026-02-20）。
         - [x] 置換後に `--help` / `.json` 入力の既存経路が壊れないことを確認する。: `./selfhost/py2cpp.out --help` と `./selfhost/py2cpp.out <EAST.json> -o out.cpp` を確認済み（2026-02-20）。
         - [x] `.py` 入力失敗時のエラー分類を `user_syntax_error` / `input_invalid` / `not_implemented` で再点検する。: 現在は `.py` -> `not_implemented`、`.json` -> `input_invalid`、`--help` は `0` を確認済み。
       - [x] `src/py2cpp.py` の EAST 読み込み import を `pytra.compiler.east` facade から `pytra.compiler.east_parts.core` へ切り替えた（selfhost 時の動的 import 依存を削減）。
       - [x] `tools/build_selfhost.py` の現行失敗要因を段階解消する（`literal.join` 生成崩れ、`AUG_OPS/BIN_OPS` 未束縛、`parse_py2cpp_argv` 返り値の tuple 退化）。: 2026-02-20 時点で `python3 tools/build_selfhost.py` が再び green（`selfhost/py2cpp.out` 生成成功）。
         - [x] `CppEmitter._module_source_path_for_name` の selfhost 変換で `Path` が `float64` 退化する経路を除去する（`Path /` と `str + Path` を使わない）。: `Path` 合成を文字列経由へ変更し、`py_div(Path, str)` 発生を除去。
         - [x] `CppEmitter._module_function_arg_types` の `load_east` 依存を selfhost 最小モードで無効化する（`not_implemented` のままでもビルド通過を優先）。: runtime `.py` の関数シグネチャ抽出を source 解析経由のみに固定。
         - [x] `parse_py2cpp_argv` の返り値が tuple 退化する経路を修正し、`_dict_str_get(parsed, ...)` 呼び出しを常に `dict[str, str]` で通す。
         - [x] `", ".join(...)` / `" && ".join(...)` など literal `.join` が C++ 側で `char[]` 扱いになる箇所を全置換する（`sep` 変数経由または `py_join` 経由）。: `src/py2cpp.py` の結合処理を `_join_str_list(...)` 経由へ統一。
         - [x] `BIN_OPS` / `AUG_OPS` / `CMP_OPS` の global 参照が selfhost で未束縛になる経路を切り分け、`CodeEmitter` 側 accessor 経由へ寄せる。: selfhost source 準備時に `BIN_OPS/CMP_OPS/AUG_OPS/AUG_BIN` を再束縛し、`dict_get_node` の `dict[str,str]` 取得経路を runtime へ追加。
       - [ ] `src/pytra/compiler/east_parts/core.py` の selfhost 非対応構文（bootstrap/path 操作）を切り離して取り込み可能にする。
         - [x] bootstrap 専用コードを `src/pytra/compiler/east.py` facade 側へ隔離し、`east_parts.core` から除去する。
         - [x] `east_parts.core` の import を `pytra.std.*`（または同等 shim）に固定する。
         - [ ] `tools/prepare_selfhost_source.py` の取り込み対象へ `east_parts.core` を段階追加する。
       - [ ] `tools/selfhost_transpile.py` を使わず `./selfhost/py2cpp.out sample/py/01_mandelbrot.py -o /tmp/out.cpp` が成功することを確認する。
       - [ ] 上記生成物を `g++` でビルドして、実行結果が Python 実行と一致することを確認する。
3. [ ] CodeEmitter hook 移管の再開（selfhostを壊さない手順）
   - [x] `CodeEmitter` に hooks 辞書呼び出しを導入する前に、selfhost非対応構文（`callable` など）を使わない制約版APIを定義する。
     - [x] hook シグネチャを `dict[str, Any]` / `list[str]` のみで完結させる（`callable` 注釈禁止）。
     - [x] 制約版 API の最小仕様を `docs/spec-language-profile.md` へ追記する。
   - [ ] `cpp_hooks.py` は最初に `png/gif` のみ移管し、`py2cpp.py` の既存分岐を1件ずつ削る。
     - [x] `png.write_rgb_png` の解決ロジックを `cpp_hooks.py` へ移し、`py2cpp.py` 側の分岐を削除する。: `CodeEmitter.hook_on_render_call` に実配線を追加し、`_render_special_runtime_call` 系分岐を削除済み。
     - [x] `gif.save_gif` の解決ロジックを `cpp_hooks.py` へ移し、`py2cpp.py` 側の分岐を削除する。: `runtime_call`/`Name`/`Attribute` の解決は `build_cpp_hooks()` 注入の `on_render_call` 側へ統一済み。
     - [x] 補足: `cpp_hooks.py` 側の `on_render_call` 追加は着手済み。`pytra.*` 名へ正規化する処理を追加済み。selfhost を壊さない hook 呼び出し経路（高階関数を使わない方式）を先に確定する。
    - [x] 置換ごとに `tools/check_py2cpp_transpile.py` を実行し、差分を確認する。: 2026-02-20 時点で `checked=119 ok=119 fail=0 skipped=5` を確認。
   - [x] 各ステップで `tools/build_selfhost.py` と `tools/check_py2cpp_transpile.py` の両方を必須ゲートにする。
     - [x] 上記 2 コマンド失敗時はコミット禁止ルールを `docs/spec-codex.md` に明記する。

## CodeEmitter 化（JSON + Hooks）

4. [ ] フック注入 (`EmitterHooks`) を実装する。
   - [x] `on_render_call`, `on_render_binop`, `on_emit_stmt` など最小フック面を定義する。
   - [ ] `render_expr(Call/BinOp/Compare)` の巨大分岐を hooks + helper へ段階分離する。: `BinOp` + `Call(Name/Attribute)` は helper 分離済み
    - [x] `render_expr(IfExp/List/Tuple/Set/Dict/Subscript)` を `hook_on_render_expr_kind(kind, node)` へ委譲できる形へ整理する。: `render_expr` 先頭で kind フックを共通呼び出しする形へ移行済み。
    - [x] `JoinedStr/Lambda/Comp` 系を `hook_on_render_expr_complex(node)` へ分離する。: 入口フックを実装し、`JoinedStr/Lambda/ListComp/SetComp/DictComp` で委譲可能化。
   - [x] `emit_stmt(If/While/For/AnnAssign/AugAssign)` の分岐を hooks + template helper へ段階分離する。: `If/While` は `_emit_if_stmt` / `_emit_while_stmt`、`For` はヘッダ template 化、`AnnAssign/AugAssign` は文面 template 化、`hook_on_emit_stmt_kind` 入口で kind 単位の差し替えが可能。
    - [x] `emit_stmt(Return/Expr/Assign/Try)` を `hook_on_emit_stmt_kind(kind, stmt)` 前提で分割する。
    - [x] `emit_stmt` 本体を「dispatch + fallback」のみ（50行以下目標）へ縮退する。
   - [ ] profile で表現しにくいケースのみ hooks 側へ寄せる（`py2cpp.py` に条件分岐を残さない）。
   - [x] C++ 向け hooks 実装を `src/hooks/cpp/hooks/cpp_hooks.py` として分離する。

## py2cpp 縮退（行数削減）

1. [ ] `src/py2cpp.py` の未移行ロジックを `CodeEmitter` 側へ移し、行数を段階的に削減する。
   - [x] 目標値を固定する（`src/py2cpp.py` 実コード 1500 行以下を当面目標）。
   - [x] ベースライン行数を計測し、`docs/todo.md` に記録する（毎回更新）。: 2026-02-19 時点 `src/py2cpp.py` は `4305` 行（`wc -l`）
   - [ ] `render_expr` の `Call` 分岐（builtin/module/method）を機能単位に分割し、`CodeEmitter` helper へ移す。: `BuiltinCall` / Name/Attribute は helper 分離済み
     - [ ] `dict.get/list.* / set.*` 呼び出し解決を runtime-call map + hook へ移して `py2cpp.py` 直書きを削減する。
     - [x] `Path`/`png`/`gif` の module method 解決を `cpp_hooks.py` 側へ寄せる。: `png/gif` は `Call` + `Attribute`、`Path` は `Attribute(name/stem/parent)` を hooks 移管済み。
   - [x] `render_expr` の `Call` で残っている module method / object method / fallback 呼び出しを 3 helper に分離する。
   - [x] `render_expr` の `Call` で runtime-call 解決前後の前処理（kw 展開・owner 抽出）を helper 化する。
   - [x] `render_expr` の `Call` 分岐を 200 行未満に縮退する（目標値を明示）。: 現在は helper 呼び出し中心で 20 行前後
   - [ ] `render_expr` の算術/比較/型変換分岐を独立関数へ分割し、profile/hook 経由で切替可能にする。: `BinOp` / `Compare` / `UnaryOp` は専用 helper に分離済み
     - [x] `IfExp` の cast 適用ロジックを helper 化する。
    - [ ] `Constant(Name/Attribute)` の基本レンダを `CodeEmitter` 共通へ移す。: `Name` の予約語リネームは `CodeEmitter.rename_if_reserved(...)` へ移管済み
   - [x] `Compare` 分岐を helper へ切り出す（`Contains` / chain compare / `is` 系）。
   - [x] `UnaryOp` と `BoolOp` の条件式特化ロジックを helper へ切り出す。: `UnaryOp` は `_render_unary_expr` へ分離、`BoolOp` は既存 `render_boolop` を継続利用
   - [x] `Subscript` / `SliceExpr` / `Concat` を helper 化し、`render_expr` 直書きを削減する。: `Subscript`/`SliceExpr` は `_render_subscript_expr` へ分離（`Concat` は既存 helper 経路）
   - [ ] `emit_stmt` の制御構文分岐をテンプレート化して `CodeEmitter.syntax_*` へ寄せる。: `If/While` は専用 helper に分離済み
     - [ ] `syntax.if/elif/else`, `syntax.while`, `syntax.for_range`, `syntax.for_each` の最小テンプレート定義を profile へ追加する。
     - [ ] C++ 固有差分（brace省略や range-mode）だけ hook 側で上書きする。
   - [x] `For` / `AnnAssign` / `AugAssign` を helper 化して `emit_stmt` 本体を縮退する。: `For` は既存 `emit_for_each`/`emit_for_range`、`AnnAssign`/`AugAssign` は helper 分離済み
   - [ ] `FunctionDef` / `ClassDef` の共通テンプレート（open/body/close）を `CodeEmitter` 側に寄せる。: `open/close` helper は移管済み。`body` 側は `emit_scoped_stmt_list` / `emit_with_scope` / `emit_scoped_block` を導入し、`If/While/ForRange/FunctionDef` へ適用済み。`ClassDef` 本体適用を継続する。
2. [ ] 未使用関数の掃除を継続する（詳細タスクは「最優先（即時）」へ移動）。
   - [x] `extract_module_leading_trivia` ラッパーを削除。
   - [x] `_stmt_start_line` / `_stmt_end_line` / `_has_leading_trivia` を削除。
   - [x] `py2cpp.py` 内の補助関数で参照ゼロのものを追加洗い出しして削除する。: `_safe_nested_dict` / `_safe_nested_str_map` / `_safe_nested_str_list` / `_load_cpp_runtime_call_map_json` を削除

## selfhost 回復（後段）

1. [ ] `CodeEmitter` の `Any/dict` 境界を selfhost で崩れない実装へ段階移行する。
   - [x] `any_dict_get` / `any_to_dict` / `any_to_list` / `any_to_str` の C++ 生成を確認し、`object.begin/end` 生成を消す。
   - [x] `render_cond` / `get_expr_type` / `_is_redundant_super_init_call` で `optional<dict>` 混入をなくす。
     - [x] `get_expr_type` は `resolved_type` の動的値フォールバックを追加し、selfhost 変換時の空文字化を抑制した（2026-02-20）。
     - [x] `_is_redundant_super_init_call` は `dict` 正規化と `kind` 取得の共通化（`_node_kind_from_dict`）で `Any/object` 境界でも安定化した（2026-02-20）。
     - [x] `render_cond` の同等整理（`optional<dict>` 境界の削減）を実施した。: `repr` の動的値フォールバックと外側括弧除去を追加し、`test/unit/test_code_emitter.py` で回帰固定（2026-02-20）。
     - [x] `render_expr` の先頭正規化で `expr_node` 再代入パターンを除去し、`object -> dict` を1回に固定する。: `kind` 取得を `_node_kind_from_dict` に統一し、手書き fallback 再代入を削減（2026-02-20）。
     - [x] `*_dict_stmt_list` 系引数を `expr.get(..., [])` ではなく `expr.get(...)` + helper 正規化へ統一する。: `dict.get(..., [])` 残存3件（`details`/`graph_adj`）を helper 経由へ置換（2026-02-20）。
   - [x] `test/unit/test_code_emitter.py` に selfhost 境界ケース（`None`, `dict`, `list`, `str`）を追加する。
   - [x] `emit_leading_comments` / `emit_module_leading_trivia` で `Any` 経由をやめ、list[dict] 前提に統一する。
   - [x] `hook_on_*` 系の `hooks` コンテナ型を selfhost で安定化する。
     - [x] `CodeEmitter` 側の hook 呼び出しを object receiver メソッド参照（`self.hooks.on_*`）から排除する。
     - [x] `selfhost/py2cpp.cpp` で `hooks` が `object` へ退化しないよう、`dict[str, Any]` を維持する初期化経路へ統一する。: `CodeEmitter.hooks` を `dict[str, Any]` へ固定し、`selfhost/py2cpp.cpp` で `inline static dict<str, object> hooks;` を確認（2026-02-20）。
     - [x] `fn(self, ...)` 呼び出しが C++ 側で無効式になる問題を、selfhost 生成時 hook no-op 化で解消した。: `tools/prepare_selfhost_source.py` による置換後 `selfhost/py2cpp.cpp` で `hook_on_*` は `nullopt` 返却のみ（2026-02-20）。
   - [ ] `*_dict_get*` の default 引数を `str` / `int` / `list` 別 helper に分離し、`object` 強制変換を減らす。
     - [x] `any_dict_get_bool` / `any_dict_get_list` / `any_dict_get_dict` を追加する。
     - [ ] `py_dict_get_default(..., list<object>{})` を全箇所削減する（selfhost compile logで追跡）。
   - [x] `split_*` / `is_*_type` の引数型を `str` に固定し、`py_slice(object,...)` 生成を消す。
2. [ ] `cpp_type` と式レンダリングで `object` 退避を最小化する。
   - [ ] `str|None`, `dict|None`, `list|None` の Union 処理を見直し、`std::optional<T>` 優先にする。
   - [ ] `Any -> object` が必要な経路と不要な経路を分離し、`make_object(...)` の過剰挿入を減らす。
   - [ ] `py_dict_get_default` / `dict_get_node` の既定値引数が `object` 必須になる箇所を整理する。
   - [ ] `py2cpp.py` で `nullopt` を default 値に渡している箇所を洗い出し、型ごとの既定値へ置換する。
   - [ ] `std::any` を経由する経路（selfhost 変換由来）をログベースでリスト化し、順次削除する。
     - [ ] `tools/summarize_selfhost_errors.py` 出力の `cannot convert std::any` 発生行をホットスポット表に集約する。
     - [ ] 上位3関数ごとにパッチを分けて改善し、毎回 `check_py2cpp_transpile.py` を通す。
3. [ ] selfhost コンパイルエラーを段階的にゼロ化する。
   - [x] `selfhost/build.all.log` の先頭 200 行を優先して修正し、`total_errors < 300` にする。: 2026-02-18 再計測で `total_errors=82`
   - [x] 同手順で `total_errors < 100` まで減らす。: 2026-02-18 再計測で `total_errors=82`
   - [x] `total_errors <= 50` にする。: 2026-02-19 再計測で `total_errors=25`
   - [x] `total_errors <= 20` にする。: 2026-02-19 再計測で `total_errors=17`
   - [x] `total_errors = 0` にする。: 2026-02-19 再計測で C++ `error:` は 0（残りは単体リンク時の `ld` エラー）
   - [x] 段階ゲート A: `total_errors <= 450` を達成し、`docs/todo.md` に主因更新。: 2026-02-18 再計測で `total_errors=322`
   - [x] 段階ゲート B: `total_errors <= 300` を達成し、同時に `test_code_emitter` 回帰を固定化。: 2026-02-18 再計測で `total_errors=233`、`test/unit/test_code_emitter.py` は 12/12 pass
   - [x] 段階ゲート C-1: `total_errors <= 100` を維持する。: 2026-02-19 再計測で `total_errors=72`
   - [x] 段階ゲート C-2: `tools/check_selfhost_cpp_diff.py` の最小ケースを通す。: `--mode allow-not-implemented` で `mismatches=0`
4. [ ] `selfhost/py2cpp.out` を生成し、最小実行を通す。
   - [x] `tools/build_selfhost.py` を追加し、runtime `.cpp` を含めて `selfhost/py2cpp.out` を生成できるようにする。
   - [x] `selfhost/py2cpp.out` は `__pytra_main(argv)` を実行する状態まで接続する（no-op ではない）。
   - [ ] `./selfhost/py2cpp.out sample/py/01_mandelbrot.py test/transpile/cpp2/01_mandelbrot.cpp` を成功させる。
     - [ ] 引数パース互換（`INPUT OUTPUT` 形式）と `-o` 形式の両方で通ることを確認する。
       - [x] `argv[0]` 混入で `unexpected extra argument` になる不具合を修正し、`-o` 形式で `not_implemented` まで到達することを確認する（2026-02-19）。
      - [x] `parse_py2cpp_argv` が `INPUT OUTPUT` 形式（`-o` 省略）を受理するように実装した（2026-02-19）。
      - [x] 失敗時に `user_syntax_error` / `input_invalid` / `not_implemented` の分類が維持されることを確認する。: selfhost 実行で `.py` と `.json` の分類を確認済み（2026-02-19）。
   - [x] `./selfhost/py2cpp.out --help` を通す。
   - [ ] `./selfhost/py2cpp.out INPUT.py -o OUT.cpp` を通す。
   - [ ] 出力された C++ をコンパイル・実行し、Python 実行結果と一致確認する。
   - [ ] `test/fixtures/arithmetic/add.py`（軽量ケース）でも selfhost 変換を実行し、最小成功ケースを確立する。
   - [ ] `tools/prepare_selfhost_source.py` の selfhost 専用スタブ整理を継続する。
     - [x] `load_east` を `.json` `input_invalid` / `.py` `not_implemented` に分割した（selfhost 最小モード）。
     - [x] selfhost parser 非対応のネスト関数を含む補助関数（import graph / multi-file）の一部をスタブへ置換した。
     - [ ] `Path`/`json` 操作の型退化で C++ 生成が崩れる箇所を段階的に縮退し、`tools/build_selfhost.py` を再 green 化する。
     - [x] `tools/build_selfhost.py` は再度 green（`selfhost/py2cpp.out` 生成成功）へ回復した。現在の制約: selfhost 実行時の `.py` 入力は `not_implemented`。
5. [ ] selfhost 版と Python 版の変換結果一致検証を自動化する。
   - [x] 比較対象ケース（`test/fixtures` 代表 + `sample/py` 代表）を決める。: `test/fixtures/core/add.py`, `test/fixtures/control/if_else.py`, `sample/py/01_mandelbrot.py`
   - [x] `selfhost/py2cpp.out` と `python3 src/py2cpp.py` の出力差分チェックをスクリプト化する。: `tools/check_selfhost_cpp_diff.py`
   - [x] CI 相当手順（ローカル）に組み込む。: `tools/run_local_ci.py`

## 複数ファイル構成（最終ゴール）

1. [ ] 依存解決フェーズを追加する。
   - [x] `import` / `from ... import ...` を収集してモジュール依存グラフを作る。: `--dump-deps` の `graph` 出力で可視化
     - [x] 相対 import（`from .mod import x`）の解決ルールを仕様化する。: 現状は未対応として `input_invalid` 扱い
     - [x] 循環 import 検出時のエラー分類を `input_invalid` で統一する。
   - [x] `pytra.*` とユーザーモジュールの探索パス解決（重複・循環検出）を実装する。
     - [x] 同名モジュール衝突時の優先順位（ユーザー/`pytra`）を仕様化して実装する。: `pytra` 名前空間予約（ユーザー側 `pytra.py` / `pytra/__init__.py` 禁止）
   - [x] 依存グラフを `--dump-deps` などで可視化できるようにする。: `src/py2cpp.py --dump-deps`
## 直近メモ

- 進捗: `except ValueError:` 受理と `return`（値なし）受理を self_hosted parser に追加し、EAST 生成は通過。
- 現在の主要原因（2026-02-18 再計測）:
  1. `BaseEmitter.any_dict_get` が `optional<dict>` に対して `.find/.end` を生成してしまう。
  2. `Any -> object` 変換の影響で、`""` / `list{}` / `nullopt` を default 引数に渡す箇所が大量に不整合化している。
  3. `render_expr` 系 API が `dict|None` 固定のため、selfhost 生成側で `object/std::any` から呼び出した時に詰まる。
  4. 方針として selfhost 専用 lowering は極力増やさず、型付き helper と runtime 補助 API の拡充で汎用的に解消する。
- 更新（2026-02-18）:
  1. `BaseEmitter`（移行後 `CodeEmitter`）側の `any_*` を明示 `if` へ書き換え、ifexp（三項演算子）由来の不整合を削減する下準備を実施。
  2. `selfhost/py2cpp.py` と `selfhost/runtime/cpp/*` を `src` 最新へ同期済み。
  3. 依然として主因は `object` / `optional<dict>` / `std::any` の境界変換（代入・引数渡し・`py_dict_get_default` 呼び出し）に集中している。
- 更新（2026-02-18 selfhost 追加）:
  1. `tools/prepare_selfhost_source.py` を追加し、`src/pytra/compiler/east_parts/code_emitter.py` を `selfhost/py2cpp.py` へ自動インライン展開できるようにした。
  2. `python3 src/py2cpp.py selfhost/py2cpp.py -o selfhost/py2cpp.cpp` は再び通過するようになった。
  3. 現在の主因は `Any/object` 境界由来の C++ 型不整合（2026-02-18 再計測で `total_errors=82`）。
  4. 先頭エラー群は `emit_stmt`/`emit_stmt_list` の文リスト型、`render_boolop` 周辺の `Any` 取り回し、`self` 記号解決の C++ 生成不整合が中心。
  5. 解析補助:
     - `python3 tools/summarize_selfhost_errors.py selfhost/py2cpp.compile.log`
     - `python3 tools/selfhost_error_hotspots.py selfhost/py2cpp.cpp selfhost/py2cpp.compile.log`
  6. 2026-02-18 時点の上位ホットスポット（`selfhost_error_hotspots.py`）:
     - `render_expr`: `69`
     - `emit_class`: `17`
     - `emit_assign`: `15`
- 更新（2026-02-19 selfhost 進捗）:
  1. `tools/prepare_selfhost_source.py` -> `src/py2cpp.py selfhost/py2cpp.py` は継続して通過。
  2. selfhost C++ の型エラー（`error:`）は解消済み。単体リンク失敗は runtime `.cpp` 同時リンクで解消。
  3. 現在の selfhost 実行時は `load_east` スタブのため、`.py` 入力は `[not_implemented]`、`.json` 入力は `[input_invalid]` を返す（設計通りの暫定動作）。
  4. `--help` は selfhost 実行で終了コード `0` で表示されるように修正済み（`parse_py2cpp_argv` の `continue` 依存を回避）。
  5. `a in {"x","y"}` の selfhost C++ 生成は一時オブジェクト生成の都合で不安定なため、CLI 解析経路では `a == "x" or a == "y"` を採用。
  6. `tools/check_selfhost_cpp_diff.py` に `--mode allow-not-implemented`（既定）を追加し、現段階の selfhost 未実装ケースを skip 集計できるようにした。
  7. `py_runtime.h` の `optional<dict<...>>` 向け `py_dict_get` が temporary 参照返却警告を出していたため、値返しへ変更して selfhost ビルド警告を解消。
  8. `tools/run_local_ci.py` を追加し、`check_py2cpp_transpile` / unit tests / selfhost build / selfhost diff（allow-not-implemented）を1コマンドで実行できるようにした。
  9. selfhost の `load_east` に `.json` 入力経路を追加し、当時は C++ runtime 経由で EAST JSON を直接読み込めるようにした（現在は pure Python 実装の正本化方針へ移行中）。
  10. `CppEmitter` 生成時の `CodeEmitter` 基底初期化を `load_cpp_profile()` 付きに修正し、selfhost での `dict key not found: syntax` を解消した。
  11. `tools/selfhost_transpile.py` を追加し、`.py` 入力を一時 EAST JSON 化して selfhost バイナリに渡す暫定運用を可能にした。
  12. selfhost JSON 直入力時の改行崩れ（`\\n` がそのまま出る問題）を修正し、通常の改行付き C++ 出力へ回復した。
  13. selfhost 生成 C++ で関数本体が空になる問題（`emit_stmt_list` の基底 no-op 束縛）を解消し、`return`/式文が出力されるようにした。
  14. selfhost 生成 C++ の `print(...)` 残留を暫定修正し、フォールバックでも `py_print(...)` を出力するようにした。
  15. `tools/check_selfhost_cpp_diff.py --selfhost-driver bridge` の `sample/py/01_mandelbrot.py` 差分を解消（引数順崩れ/`png.write_rgb_png` 残留/浮動小数リテラル差分を修正）。
  16. `test/fixtures/collections/comprehension_filter.py` の selfhost 差分を解消（内包表現 `if` 条件崩れと `list[bool]` 初期化型崩れを修正）。
  17. `tools/check_selfhost_cpp_diff.py --selfhost-driver bridge` の既定ケースで `mismatches=0` を確認。
  2. `g++` コンパイルエラーは `total_errors=72`（`<=100` 維持）を確認。
  3. 現在の上位は `__pytra_main`（import/runtime 参照境界）と `emit_class` / `emit_assign` の `Any` 境界由来の型不整合。
