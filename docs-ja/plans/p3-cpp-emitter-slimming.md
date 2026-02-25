# P3: C++ emitter 肥大化の段階縮退

最終更新: 2026-02-25

関連 TODO:
- `docs-ja/todo/index.md` の `ID: P3-CPP-EMITTER-SLIM-01`

背景:
- `src/hooks/cpp/emitter/cpp_emitter.py` は約 6.6k 行規模で、`render_expr` の分岐集中と C++ 固有責務の同居により変更衝突が起きやすい。
- EAST3 主経路を採用している一方で、`stage2/self_hosted` 互換・legacy type_id 名呼び出しなどの互換分岐が残っている。
- import/include/namespace/class/type/runtime-call などの責務が単一ファイルへ集中し、局所変更でも回帰範囲が広い。

目的:
- `cpp_emitter.py` を「オーケストレーション + ディスパッチ」中心へ縮退し、互換層を撤去した EAST3 単一契約へ寄せる。

対象:
- `src/hooks/cpp/emitter/cpp_emitter.py`
- `src/hooks/cpp/emitter/` 配下（`call.py` / `expr.py` / `stmt.py` / `operator.py` / `tmp.py` / `trivia.py` と新規分割モジュール）
- 必要時: `src/pytra/compiler/east_parts/code_emitter.py`（共通化対象のみ）
- テスト/検証: `test/unit/test_py2cpp_*.py`, `tools/check_py2cpp_transpile.py`, `tools/check_selfhost_cpp_diff.py`, `tools/verify_selfhost_end_to_end.py`

非対象:
- C++ runtime API の仕様変更
- sample プログラム仕様の変更
- 非C++ emitter の機能追加（別タスク管理）

受け入れ基準:
- `stage2/self_hosted` 互換の C++ emitter 内 legacy 分岐（builtin/type_id/For bridge）が撤去され、EAST3 契約に統一される。
- `render_expr` がディスパッチ中心に縮退し、巨大分岐を局所 handler へ分離できる。
- `cpp_emitter.py` の最終メトリクスを記録し、少なくとも以下を満たす。
  - ファイル行数: 2500 行以下（目安）
  - `render_expr` 行数: 200 行以下（目安）
  - legacy 互換関数残数: 0
- C++ 回帰（unit/smoke/selfhost）が基線を維持する。

## 分解

- [ ] [ID: P3-CPP-EMITTER-SLIM-01-S1-01] `cpp_emitter.py` の行数・メソッド数・長大メソッドを計測し、基準値を文書化する。
- [ ] [ID: P3-CPP-EMITTER-SLIM-01-S1-02] `sample` と `test/unit` の C++ 生成差分基線を固定する。
- [ ] [ID: P3-CPP-EMITTER-SLIM-01-S2-01] stage2/self_hosted 由来の legacy builtin compat 経路を撤去する。
- [ ] [ID: P3-CPP-EMITTER-SLIM-01-S2-02] `For`/`ForRange` <-> `ForCore` bridge を撤去し、`ForCore` 直接受理へ統一する。
- [ ] [ID: P3-CPP-EMITTER-SLIM-01-S2-03] legacy `isinstance/issubclass` Name-call 許容を撤去し、type_id 系を EAST3 ノード前提に統一する。
- [ ] [ID: P3-CPP-EMITTER-SLIM-01-S3-01] import/include/namespace/module-init の責務を専用モジュールへ分離する。
- [ ] [ID: P3-CPP-EMITTER-SLIM-01-S3-02] class emit（`virtual/override`・`PYTRA_TYPE_ID`）責務を専用モジュールへ分離する。
- [ ] [ID: P3-CPP-EMITTER-SLIM-01-S3-03] 型変換 (`_cpp_type_text`) と Any 境界補正 helper を専用モジュールへ分離する。
- [ ] [ID: P3-CPP-EMITTER-SLIM-01-S3-04] built-in runtime_call（list/set/dict/str/path/special）分岐を専用ディスパッチへ分離する。
- [ ] [ID: P3-CPP-EMITTER-SLIM-01-S4-01] `render_expr` の `kind -> handler` テーブル駆動の骨格を導入する。
- [ ] [ID: P3-CPP-EMITTER-SLIM-01-S4-02] collection literal/comprehension 系 handler を分離し、回帰テストを追加する。
- [ ] [ID: P3-CPP-EMITTER-SLIM-01-S4-03] runtime/type_id/path 系 handler を分離し、`render_expr` をディスパッチ専任へ縮退する。
- [ ] [ID: P3-CPP-EMITTER-SLIM-01-S5-01] `repr` 依存ノードの対象を棚卸しし、parser/lowerer 側の構造化ノード移行計画を確定する。
- [ ] [ID: P3-CPP-EMITTER-SLIM-01-S5-02] `_render_repr_expr` の利用箇所を段階削減し、最終 fallback 以外を除去する。
- [ ] [ID: P3-CPP-EMITTER-SLIM-01-S5-03] `_render_repr_expr` を撤去（または no-op 化）し、`repr` 文字列依存をなくす。
- [ ] [ID: P3-CPP-EMITTER-SLIM-01-S6-01] Rust/C++ 共通化候補（条件式・cast 補助・ループ骨格）を棚卸しし、`CodeEmitter` 移管対象を確定する。
- [ ] [ID: P3-CPP-EMITTER-SLIM-01-S6-02] 共通化対象の 1〜2 系統を `CodeEmitter` へ移管し、C++/Rust の重複を削減する。
- [ ] [ID: P3-CPP-EMITTER-SLIM-01-S7-01] `test/unit/test_py2cpp_*.py` と `tools/check_py2cpp_transpile.py` を通して回帰を固定する。
- [ ] [ID: P3-CPP-EMITTER-SLIM-01-S7-02] `tools/check_selfhost_cpp_diff.py` / `tools/verify_selfhost_end_to_end.py` で selfhost 回帰を確認する。
- [ ] [ID: P3-CPP-EMITTER-SLIM-01-S7-03] 最終メトリクスを再計測し、完了判定（行数・`render_expr` 行数・legacy 0件）を記録する。

決定ログ:
- 2026-02-25: `cpp_emitter.py` の肥大要因分析（互換層残存 + 責務集中 + 巨大 `render_expr`）に基づき、低優先の段階縮退タスクとして追加。
