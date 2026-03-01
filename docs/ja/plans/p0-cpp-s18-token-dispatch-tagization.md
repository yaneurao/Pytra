# P0: sample/18 tokenizer の文字列分岐を tag 化（if連鎖縮退）

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-S18-TOKEN-DISPATCH-TAG-01`

背景:
- sample/18 の tokenizer は `if (ch == "+") ...` の文字列比較連鎖で token kind を決めている。
- 分岐が増えるほど比較コストと生成コードの冗長性が増える。

目的:
- tokenizer の token 判定を tag/enum ベースへ段階移行し、文字列比較連鎖を縮退する。

対象:
- `src/hooks/cpp/emitter/*`（tokenize 出力）
- `sample/py/18_mini_language_interpreter.py`（必要最小の型注釈調整が必要な場合のみ）
- `test/unit/test_py2cpp_codegen_issues.py`
- `sample/cpp/18_mini_language_interpreter.cpp`

非対象:
- mini language 文法拡張
- parser/evaluator 全面再設計

受け入れ基準:
- sample/18 の tokenizer で token kind 決定が tag 参照中心になり、長い文字列 if 連鎖が縮退する。
- エラーメッセージ用途の kind 文字列は必要最小で維持される。
- transpile/unit/parity で非退行を確認する。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/runtime_parity_check.py --case-root sample --targets cpp 18_mini_language_interpreter --ignore-unstable-stdout`

決定ログ:
- 2026-03-01: sample/18 追加最適化として tokenizer 分岐の tag 化を P0 で起票。

## 分解

- [ ] [ID: P0-CPP-S18-TOKEN-DISPATCH-TAG-01] tokenizer の kind 判定を文字列比較連鎖から tag/enum 中心へ移行する。
- [ ] [ID: P0-CPP-S18-TOKEN-DISPATCH-TAG-01-S1-01] 現在の分岐列を棚卸しし、tag マップ（1文字->kind_tag）仕様を固定する。
- [ ] [ID: P0-CPP-S18-TOKEN-DISPATCH-TAG-01-S2-01] emitter 出力を tag 判定優先へ変更し、同値な kind 文字列は必要箇所のみ残す。
- [ ] [ID: P0-CPP-S18-TOKEN-DISPATCH-TAG-01-S2-02] sample/18 回帰を追加し、`if (ch == "...")` 連鎖の再発を防止する。
- [ ] [ID: P0-CPP-S18-TOKEN-DISPATCH-TAG-01-S3-01] transpile/unit/parity で非退行を確認する。
