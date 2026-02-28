# P0: EAST3 モジュール横断 non-escape 解析（import 先本文を含む）

最終更新: 2026-02-28

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-EAST3-XMOD-NONESCAPE-01`

背景:
- 現行の `NonEscapeInterproceduralPass` は同一 Module 内の `FunctionDef/ClassDef` のみを解析対象にしている。
- そのため `save_gif(...)` のような import 先関数は未解決 call になり、既定 policy（fail-closed）で引数 escape 扱いになる。
- 結果として C++ emitter 側では `frames: list[bytes]` が non-escape と判定できず、`object` へ退化するケースが残る。

目的:
- EAST3 non-escape 解析をモジュール横断（import closure）へ拡張し、import 先の関数本体を含めた call graph で summary を計算する。
- `escape contract` の手書き定義は導入せず、実際のソース本文だけで判定する。

対象:
- `src/pytra/compiler/east_parts/east3_opt_passes/non_escape_call_graph.py`
- `src/pytra/compiler/east_parts/east3_opt_passes/non_escape_interprocedural_pass.py`
- import 解決周辺（必要に応じて `core.py` / `transpile_cli.py` / EAST3 doc meta）
- `src/hooks/cpp/emitter/cpp_emitter.py`（safe-call 固定判定の縮退）
- `test/unit/test_east3_non_escape_*`
- `test/unit/test_py2cpp_*` と `tools/check_py2cpp_transpile.py`
- `sample/cpp/05_mandelbrot_zoom.cpp` の再生成確認

非対象:
- 手書き `escape contract` registry の新設
- 他 backend（Rust/Java/Go など）の escape 最適化適用
- alias 解析や points-to 解析の高度化

受け入れ基準:
- import 先関数を含む call graph が構築され、`non_escape_summary` がモジュール横断で収束する。
- `save_gif` を呼ぶ `sample/05` 経路で `frames` が non-escape と判定され、C++ 生成で `list<bytes>`（または等価な value 型）を維持できる。
- 未解決 import や循環 import を含むケースでも fail-closed を維持し、クラッシュせず決定的に収束する。
- 既存の `east3 optimizer` / `py2cpp` 回帰が非退行で通る。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_non_escape_*.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_optimizer*.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_*.py' -v`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/regenerate_samples.py --langs cpp --force`
- `rg -n "frames|save_gif|list<bytes>|object frames" sample/cpp/05_mandelbrot_zoom.cpp`

決定ログ:
- 2026-02-28: ユーザー指示により、`escape contract` 方式は採用せず、モジュール横断 call graph による non-escape 判定へ一本化する方針を確定した。

## 分解

- [x] [ID: P0-EAST3-XMOD-NONESCAPE-01-S1-01] import closure の収集仕様（対象モジュール範囲、循環時挙動、未解決時 fail-closed）を確定する。
- [x] [ID: P0-EAST3-XMOD-NONESCAPE-01-S1-02] 関数シンボルを `module_id::symbol` で一意化し、モジュール横断 call target 解決を実装する。
- [x] [ID: P0-EAST3-XMOD-NONESCAPE-01-S2-01] `NonEscapeInterproceduralPass` をモジュール横断 summary 計算へ拡張し、SCC fixed-point の決定性を維持する。
- [x] [ID: P0-EAST3-XMOD-NONESCAPE-01-S2-02] callsite `meta.non_escape_callsite` / module `meta.non_escape_summary` を横断解析結果で更新する。
- [ ] [ID: P0-EAST3-XMOD-NONESCAPE-01-S3-01] C++ emitter の safe-call 固定ホワイトリスト依存を縮退し、`non_escape_callsite` 注釈を優先して stack-list 判定できるようにする。
- [ ] [ID: P0-EAST3-XMOD-NONESCAPE-01-S3-02] `sample/05` で `frames` が `object` へ退化しないことを確認し、`save_gif` 呼び出し時の暗黙変換を削減する。
- [ ] [ID: P0-EAST3-XMOD-NONESCAPE-01-S4-01] module-cross / unresolved-import / recursive-import の回帰テストを追加し、fail-closed と決定性を固定する。
- [ ] [ID: P0-EAST3-XMOD-NONESCAPE-01-S4-02] `check_py2cpp_transpile` と C++ 回帰を実行し、非退行を確認する。

## S1-01 収集仕様（確定）

- 解析の起点は「現在の EAST3 Module 1件」。`meta.import_bindings` から依存モジュール候補を得て import closure を構築する。
- closure に含めるモジュールは `binding_kind in {module,symbol,wildcard}` の `module_id` を BFS で辿って得たものとし、同一 `module_id` は 1 回だけ展開する。
- `module_id -> source_path` 解決は「既存 import 解決結果を優先」し、未解決ならそのモジュールは closure に追加しない（fail-closed）。
- module 読み込みに失敗した場合（ファイル欠落・parse 失敗・EAST3 生成失敗）は、そのモジュールに向かう callsite を unresolved として扱い、unknown-call escape policy を適用する。
- 循環 import は `visited(module_id)` で打ち切る。SCC は call graph 側で処理し、import closure 収集側では再帰展開を行わない。
- deterministic 性のため、展開キュー投入順とモジュール処理順は `module_id` 昇順で固定する。
- summary の `symbol` key は `module_id::function` 形式へ統一し、同名関数衝突を許容する。
- 既定 policy は fail-closed。`meta.non_escape_summary` には closure 内で解析できた関数のみを書き、未解決関数は callsite `resolved=false` を保持する。
