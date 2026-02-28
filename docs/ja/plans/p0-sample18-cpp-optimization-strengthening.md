# P0: sample/18 C++ 出力最適化の強化（実行系ホットパス）

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-S18-OPT-01`

背景:
- `sample/cpp/18_mini_language_interpreter.cpp` には、動作互換を優先した `object` 経由処理が残っている。
- とくに tokenize / parse / execute のホットパスで、typed path に落とせる箇所が未縮退。
- 既存の可読性タスク（`P1-CPP-S18-READ-01`）で一部は改善済みだが、現行出力には再び動的経路が残存している。

目的:
- `sample/18` の C++ 出力で、`object` 経路と文字列判定コストを段階縮退し、実行時オーバーヘッドを削減する。
- EAST3 から型が分かる経路は typed loop / typed container / typed access を優先する。

対象:
- `src/pytra/compiler/east_parts/east3_opt_passes/*`（必要時）
- `src/hooks/cpp/emitter/*.py`（for/call/stmt/expr/type_bridge）
- `test/unit/test_east3_cpp_bridge.py`
- `test/unit/test_py2cpp_codegen_issues.py`
- `sample/cpp/18_mini_language_interpreter.cpp`（再生成確認）

非対象:
- mini language の仕様変更
- runtime ABI の全面変更
- sample/18 以外の一括最適化

受け入れ基準:
- `sample/18` で次の6点が確認できる:
  1. `enumerate(lines)` が `object` + `py_at` ではなく typed tuple 反復になる。
  2. `tokens` が `object(list<object>)` ではなく typed container で保持される。
  3. `Parser` 内の `py_at + obj_to_rc_or_raise` の重複取得が削減される。
  4. `ExprNode.kind` / `StmtNode.kind` / `op` の実行時文字列比較が enum/整数タグへ縮退する。
  5. `NUMBER` token は parse 時に毎回 `py_to_int64` せず、字句解析段で数値化済み値を利用する。
  6. `execute` の stmt 反復が typed loop（非 `object`）へ縮退する。
- `check_py2cpp_transpile.py`、`test_east3_cpp_bridge.py`、`test_py2cpp_codegen_issues.py` が通る。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_py2cpp_transpile.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 src/py2cpp.py sample/py/18_mini_language_interpreter.py -o sample/cpp/18_mini_language_interpreter.cpp`

決定ログ:
- 2026-03-01: ユーザー指示により、sample/18 C++ の最適化余地6項目を P0 として詳細分解し、実装計画を作成した。
- 2026-03-01: `cpp_list_model=pyobj` では `enumerate(lines)` が `py_enumerate(object)` 解決になって typed direct unpack へ進めないため、`iter_item_type=tuple[int64, str]` かつ `lines:list[str]` の場合のみ `py_to_str_list_from_object(lines)` を経由して typed enumerate を選ぶ方針を採用した。
- 2026-03-01: `test_py2cpp_codegen_issues.py` に `cpp_list_model="pyobj"` 前提の sample/18 回帰を追加し、`for (const auto& [line_index, source] : py_enumerate(py_to_str_list_from_object(lines)))` を固定した。
- 2026-03-01: `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`（75件）、`test_east3_cpp_bridge.py`（90件）、`python3 tools/check_py2cpp_transpile.py`（`checked=134 ok=134 fail=0 skipped=6`）を通過した。
- 2026-03-01: `tokens` 退化の主因は `cpp_list_model=pyobj` で `_cpp_type_text(list[T]) -> object` になる型境界にある。`tokenize()` 戻り値と `Parser.tokens` は関数境界を越える list のため、現行 stack-list（non-escape）縮退の対象外であることを確認した。
- 2026-03-01: `S2-02` は sample/18 先行で `list[Token]` 専用 unbox-once 経路（`tokenize -> Parser` 境界）を追加し、`py_append(make_object(...))` と `py_at + obj_to_rc_or_raise` 連鎖を段階縮退する方針に固定した。
- 2026-03-01: `Parser` の token access を棚卸しし、`py_at(this->tokens, this->pos)` 形が `peek_kind`（1箇所）/`expect`（2箇所）/`parse_primary`（1箇所）で重複することを確認した。`S3-02` は emitter 側で `_current_token()` / `_previous_token()` helper を合成し、同一 index の unbox 重複を削減する方針に固定した。
- 2026-03-01: 文字列比較の現状を固定した（`node->kind` 4箇所、`node->op` 4箇所、`stmt->kind` 2箇所）。`S4-02` では `kind/op` の string フィールドを維持しつつ `uint8` タグ併置で比較を整数化し、エラーメッセージのみ既存文字列を利用する方針にする。
- 2026-03-01: `NUMBER` は tokenize で既に `text` を切り出しているため、`S5-02` は `Token` に `int64 number_value`（非 NUMBER は 0）を追加し、字句段で1回だけ `py_to_int64` して parse 時再変換をなくす方針に固定した。
- 2026-03-01: `execute` typed loop へ接続するため、`S6-02` は `parse_program`/`execute` 境界を `list<rc<StmtNode>>` 優先に変更し、外部境界（main 呼び出し、必要なら runtime API）でのみ `object` boxing を許可する方針に固定した。
- 2026-03-01: `S6-02` として runtime に `py_to_rc_list_from_object<T>()` を追加し、ForCore(NameTarget) の `list[RefClass]` 反復で `pyobj` 強制 runtime path を typed 反復へ戻す fastpath を実装した。sample/18 の `execute` は `for (rc<StmtNode> stmt : py_to_rc_list_from_object<StmtNode>(stmts, ...))` へ縮退することを確認した。
- 2026-03-01: `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`（76件）/`test_east3_cpp_bridge.py`（90件）/`python3 tools/check_py2cpp_transpile.py`（`checked=134 ok=134 fail=0 skipped=6`）を再実行し非退行を確認した。
- 2026-03-01: `python3 tools/runtime_parity_check.py --case-root sample --targets cpp 18_mini_language_interpreter --ignore-unstable-stdout` を実行し、`[PASS] 18_mini_language_interpreter` を確認した。
- 2026-03-01: `S3-02` として sample/18 の `Parser` 実装を `current_token()/previous_token()` 補助メソッド経由に整理し、生成 C++ の `expect` で同一 index の token 取得を 1 回化した。`test_py2cpp_codegen_issues.py` に回帰を追加し、`runtime_parity_check` で挙動一致を確認した。
- 2026-03-01: `S5-02` として sample/18 の `Token` に `number_value` を追加し、`tokenize` で NUMBER のみ `int(text)` を predecode、`parse_primary` を `token_num.number_value` 参照へ切り替えた。`test_py2cpp_codegen_issues.py` と `runtime_parity_check`、`check_py2cpp_transpile` で非退行を確認した。
- 2026-03-01: `S4-02` として `ExprNode/StmtNode` へ `kind_tag/op_tag` を追加し、eval/execute の分岐を整数比較へ移行した。トップレベル定数の初期化が module init で shadow される問題を回避するため、tag 値は literal で固定した。

## 分解

- [ ] [ID: P0-CPP-S18-OPT-01] sample/18 C++ のホットパス6項目（typed enumerate / typed container / parser access / enum tag / number predecode / typed execute loop）を段階実装する。

- [x] [ID: P0-CPP-S18-OPT-01-S1-01] `enumerate(lines)` を typed tuple 反復へ縮退するため、EAST3 と C++ emitter の for-header 生成条件を整理する。
- [x] [ID: P0-CPP-S18-OPT-01-S1-02] `sample/18` tokenize ループで `for (::std::tuple<int64, str> ...)` 相当の出力を固定する回帰を追加する。

- [x] [ID: P0-CPP-S18-OPT-01-S2-01] `tokens` の型情報（`list[Token]` 相当）を parse->EAST3->emitter で保持し、`object(list<object>)` への退化条件を特定する。
- [ ] [ID: P0-CPP-S18-OPT-01-S2-02] `tokenize` / `Parser` の `tokens` を typed container 出力へ移行し、`py_append(make_object(...))` の過剰 boxing を削減する。

- [x] [ID: P0-CPP-S18-OPT-01-S3-01] `Parser.peek_kind/expect/parse_primary` の repeated `py_at + obj_to_rc_or_raise` パターンを検出し、共通 helper（token cache）方針を設計する。
- [x] [ID: P0-CPP-S18-OPT-01-S3-02] emitter 出力を token 取得1回利用へ変更し、同一 index の重複 dynamic access を削減する。

- [x] [ID: P0-CPP-S18-OPT-01-S4-01] `ExprNode.kind` / `StmtNode.kind` / `op` の比較箇所を棚卸しし、enum/整数タグ化の最小導入面（sample/18 先行）を定義する。
- [x] [ID: P0-CPP-S18-OPT-01-S4-02] C++ emitter でタグベース分岐を出力し、`if (node->kind == "...")` 連鎖を縮退する。

- [x] [ID: P0-CPP-S18-OPT-01-S5-01] `NUMBER` token の現在の文字列保持経路（tokenize->parse_primary->py_to_int64）を検証し、字句段 predecode 方針を確定する。
- [x] [ID: P0-CPP-S18-OPT-01-S5-02] `Token` の数値フィールド利用へ移行し、`parse_primary` の `py_to_int64(token->text)` を削減する。

- [x] [ID: P0-CPP-S18-OPT-01-S6-01] `execute` の stmt 反復を typed loop 化するため、`parse_program` 戻り値型と下流利用の整合を設計する。
- [x] [ID: P0-CPP-S18-OPT-01-S6-02] `for (object ... : py_dyn_range(stmts))` を typed 反復へ置換し、`obj_to_rc_or_raise<StmtNode>` のループ内変換を削減する。

- [ ] [ID: P0-CPP-S18-OPT-01-S7-01] `sample/18` 再生成差分（上記6点）を固定する golden 回帰を追加する。
- [x] [ID: P0-CPP-S18-OPT-01-S7-02] `check_py2cpp_transpile.py` / unit test / sample 実行で非退行を確認する。
