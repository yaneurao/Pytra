# P0: sample/18 C++ クラス生成の初期化リスト化

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-S18-CTOR-INITLIST-01`

背景:
- sample/18 の生成クラス（`Token`/`ExprNode`/`StmtNode`）コンストラクタは、本文で `this->field = arg;` を列挙する形式になっている。
- C++ では初期化リスト形式のほうが冗長性が低く、`const`/参照/move を扱う拡張余地も高い。
- 現在の出力は可読性と idiomatic C++ の観点で改善余地がある。

目的:
- class emitter のコンストラクタ生成を初期化リスト中心へ寄せ、sample/18 の可読性を改善する。

対象:
- `src/hooks/cpp/emitter/class_def.py` の合成コンストラクタ生成規則
- フィールド初期化順序の安定化（宣言順と一致）
- sample/18 回帰テストと再生成差分固定

非対象:
- ユーザー定義 `__init__` 本体ロジックの意味変更
- move 最適化の積極導入（本タスクはまず初期化リスト化）

受け入れ基準:
- sample/18 生成クラスの合成コンストラクタが初期化リスト形式になる。
- 既存セマンティクス（代入値・初期化順）が保持される。
- `test_py2cpp_codegen_issues.py` / `check_py2cpp_transpile.py` が通過する。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/regenerate_samples.py --langs cpp --stems 18_mini_language_interpreter --force --verbose`

決定ログ:
- 2026-03-01: ユーザー指示により、sample/18 生成クラスの初期化リスト化を `P0` で起票した。
- 2026-03-01: S1-01 として sample/18 の対象を「`__init__` 未定義クラスの合成 ctor」のみに固定し、ユーザー定義 `__init__` は非対象のままとした。
- 2026-03-01: S2-01 として class emitter の合成 ctor を本文代入から初期化リスト（宣言順）へ変更した。
- 2026-03-01: S2-02/S3-01 として回帰テストを追加し、sample/18 再生成・unit/transpile 回帰通過を確認した。

## 分解

- [x] [ID: P0-CPP-S18-CTOR-INITLIST-01-S1-01] 現行 class constructor 出力（本文代入）を棚卸しし、初期化リスト化対象と除外条件を固定する。
- [x] [ID: P0-CPP-S18-CTOR-INITLIST-01-S2-01] class emitter の合成コンストラクタ出力を初期化リスト形式へ変更する。
- [x] [ID: P0-CPP-S18-CTOR-INITLIST-01-S2-02] 回帰テストを追加し、本文代入形式の再発を検知する。
- [x] [ID: P0-CPP-S18-CTOR-INITLIST-01-S3-01] sample/18 再生成差分を固定し、transpile 回帰で非退行を確認する。
