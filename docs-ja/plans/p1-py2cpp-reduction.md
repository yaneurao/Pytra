# TASK GROUP: TG-P1-CPP-REDUCE

最終更新: 2026-02-24

関連 TODO:
- `docs-ja/todo.md` の `ID: P1-CPP-REDUCE-01` 〜 `P1-CPP-REDUCE-02`
- `docs-ja/todo.md` の `ID: P1-CPP-REDUCE-01-S1` 〜 `P1-CPP-REDUCE-01-S3`
- `docs-ja/todo.md` の `ID: P1-CPP-REDUCE-01-S3-S1` 〜 `P1-CPP-REDUCE-01-S3-S3`
- `docs-ja/todo.md` の `ID: P1-CPP-REDUCE-02-S1` 〜 `P1-CPP-REDUCE-02-S3`

背景:
- `py2cpp.py` の肥大化により、変更影響範囲が広くレビュー・回帰確認コストが高い。

目的:
- `py2cpp.py` を C++ 固有責務へ段階縮退し、共通処理は共通層へ移す。
- 全言語 selfhost を前提に、`py2cpp.py` を「C++ 向け thin adapter」に近づける。

対象:
- `CodeEmitter` 側へ移管可能なロジック
- CLI 層の責務分離
- `py2cpp.py` 内の汎用 helper（ソート/文字列整形/module 解析補助など）の共通層移管

非対象:
- selfhost 安定性を犠牲にする大規模一括整理

受け入れ基準:
- `py2cpp.py` 行数と分岐数が段階減少
- 主要テストと selfhost 検証が維持
- 汎用処理の新規追加先が `src/pytra/compiler/` 優先に統一され、`py2cpp.py` は C++ 固有コード中心になる

確認コマンド:
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/build_selfhost.py`

サブタスク実行順（todo 同期）:

1. `P1-CPP-REDUCE-01-S1`: `py2cpp.py` 内ロジックを「言語非依存」と「C++ 固有」へ分類し、移管順を確定する。
2. `P1-CPP-REDUCE-01-S2`: 言語非依存ロジックを `CodeEmitter` / `src/pytra/compiler/` へ段階移管する。
3. `P1-CPP-REDUCE-01-S3`: selfhost 差分ゼロを維持したまま `py2cpp.py` の重複分岐を削減する。
4. `P1-CPP-REDUCE-01-S3-S1`: `_emit_for_each_runtime` の Name ターゲット束縛重複を helper 化して削減する。
5. `P1-CPP-REDUCE-01-S3-S2`: `emit_for_each` / `_emit_for_each_runtime` の `omit_braces` + scope 処理骨格を共通化する。
6. `P1-CPP-REDUCE-01-S3-S3`: `emit_for_range` / `emit_for_each` のヘッダ生成・target scope 分岐を整理する。
7. `P1-CPP-REDUCE-02-S1`: 「汎用 helper 禁止 / 共通層先行抽出」の運用ルールを文書化する。
8. `P1-CPP-REDUCE-02-S2`: helper 追加の回帰を検出する lint/CI チェックを追加する。
9. `P1-CPP-REDUCE-02-S3`: 緊急 hotfix 時の例外運用と後追い抽出期限を定義する。

分類インベントリ（`P1-CPP-REDUCE-01-S1`）:

| 区分 | 主なロジック（`src/py2cpp.py`） | 判定 | 移管先/方針 | 優先度 |
| --- | --- | --- | --- | --- |
| A1 | `render_boolop` / `render_cond` / `render_ifexp_common` 系の式組み立て | 言語非依存 | `CodeEmitter` 共通 helper へ継続移管 | 高 |
| A2 | `Call` 前処理（`_prepare_call_parts` 周辺） | 言語非依存 | `CodeEmitter` へ集約済み。残差分を継続縮退 | 高 |
| A3 | `Assign`/`AnnAssign`/`AugAssign` の宣言判定・tuple lower 骨格 | 言語非依存 | `CodeEmitter` 共通 helper へ継続移管 | 高 |
| A4 | `For`/`ForRange`/`ForCore` のブロック骨格・scope push/pop | 言語非依存 | `CodeEmitter` / `east_parts` 側へ継続移管 | 高 |
| A5 | import/meta 束縛表の初期化と参照（`meta.import_bindings`） | 言語非依存 | `CodeEmitter` API を正本として維持（実施済み） | 中 |
| A6 | `EAST1/2/3` 変換前後で共有可能な lowering 前処理 | 言語非依存 | `src/pytra/compiler/east_parts/` へ段階移管 | 中 |
| A7 | 解析/CLI 補助（module 解析・deps dump 等） | 言語非依存 | `src/pytra/compiler/` 共通層へ抽出（`P1-COMP-*`） | 高 |
| C1 | `_cpp_type_text` / `cpp_type`（`rc<>`, `::std::optional`, `dict<...>` など） | C++固有 | `py2cpp.py` 残置（共通化しない） | 固定 |
| C2 | C++ runtime 呼び出し名解決（`py_*`, `pytra::...`） | C++固有 | `py2cpp.py` + `hooks/cpp` 残置 | 固定 |
| C3 | include/header/namespace/main 生成 | C++固有 | `py2cpp.py` 残置 | 固定 |
| C4 | C++ 演算子/キャスト最適化（`static_cast`, `::std::get`, `cpp_char_lit`） | C++固有 | `py2cpp.py` 残置 | 固定 |
| C5 | selfhost C++ 経路の互換分岐（静的束縛回避等） | C++固有 | 互換維持しつつ段階縮退 | 中 |

移管順確定（`P1-CPP-REDUCE-01-S1`）:

1. `A1/A3`（式・代入骨格）を `CodeEmitter` 優先で吸収する。
2. `A4/A6`（制御構文・EAST 前後処理）を `east_parts` 側へ寄せる。
3. `A7`（解析/CLI 補助）を `src/pytra/compiler/` 共通 API として切り出す。
4. `C1-C5` は C++ 専任面として維持し、共通層から逆流しない境界を固定する。

決定ログ:
- 2026-02-22: 初版作成。
- 2026-02-23: 全言語 selfhost の長期目標に合わせ、`py2cpp.py` への汎用 helper 追加を抑制して共通層先行抽出へ寄せる方針（`P1-CPP-REDUCE-02`）を追加した。
- 2026-02-23: docs-ja/todo.md の P1-CPP-REDUCE-01/02 を -S* 子タスクへ分割したため、本 plan に同粒度の実行順を追記した。
- 2026-02-24: [ID: P1-CPP-REDUCE-01-S1] `py2cpp.py` を「言語非依存（A群）」と「C++固有（C群）」へ分類し、移管順（A1/A3 -> A4/A6 -> A7 -> C群固定）を確定した。以後 `P1-CPP-REDUCE-01-S2` は A群のみを対象に進め、C群は境界維持を前提とする。
- 2026-02-24: [ID: P1-CPP-REDUCE-01-S2] `fallback_tuple_target_names_from_repr` / `target_bound_names` を `CodeEmitter` へ移管し、`py2cpp.py` 側の同名 helper を削除した。`test/unit/test_code_emitter.py` に回帰テストを追加し、`check_py2cpp_transpile` / `check_selfhost_cpp_diff --mode allow-not-implemented` で差分ゼロを確認。
- 2026-02-24: [ID: P1-CPP-REDUCE-01-S3-S1] `_emit_for_each_runtime` 内の Name ターゲット束縛分岐（`omit_braces` 有無で重複）を `_emit_for_each_runtime_target_bind` へ抽出し、重複分岐を削減した。`check_py2cpp_transpile` / `check_selfhost_cpp_diff --mode allow-not-implemented` で回帰なしを確認した。
