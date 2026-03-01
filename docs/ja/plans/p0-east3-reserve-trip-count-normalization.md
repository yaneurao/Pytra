# P0: EAST3主導 `reserve` 件数式正規化（C++ emitter文字列組み立て撤去）

最終更新: 2026-03-02

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-EAST3-RESERVE-COUNT-NORM-01`

背景:
- 現在の `reserve` 出力は、EAST3 の `reserve_hints` 判定までは最適化層で行う一方、件数式の組み立ては C++ emitter 側の文字列生成で実施している。
- そのため `sample/cpp/18_mini_language_interpreter.cpp` で `lines.reserve(((var_count) <= (0) ? 0 : (var_count) - (0)));` のような冗長な式が残る。
- ユーザー要件として、式の正規化責務を EAST3 側へ移し、backend 側は正規化済み式の描画に徹する形が求められている。

目的:
- `reserve` 件数式の正規化を EAST3 で確定し、C++ emitter の文字列組み立て依存を解消する。
- `sample/18` の `reserve` 式を可読な正規形へ縮退し、同種冗長式の再発を防止する。

対象:
- `src/pytra/compiler/east_parts/east3_opt_passes/safe_reserve_hint_pass.py`
- `src/pytra/compiler/east_parts/east3_opt_passes/*`（必要に応じて新規 pass）
- `src/hooks/cpp/emitter/stmt.py`
- `test/unit/*`（EAST3 optimizer / C++ codegen 回帰）
- `sample/cpp/18_mini_language_interpreter.cpp`（再生成結果）

非対象:
- `reserve` 対象判定の仕様変更（無条件 append + 静的 range のみ）
- C++ 以外 backend の `reserve` 出力最適化
- 一般式簡約エンジンの全面導入

受け入れ基準:
- EAST3 `reserve_hints` に件数式（ASTまたは同等の構造化表現）を保持し、C++ emitter がそれを直接描画する。
- C++ emitter から `StaticRange` 件数式の文字列組み立てロジックを撤去するか、フォールバック専用の最小経路へ縮小する。
- `sample/cpp/18_mini_language_interpreter.cpp` の `lines.reserve(...)` が `- (0)` や過剰括弧を含む旧式から更新される。
- `tools/check_py2cpp_transpile.py` と関連 unit テストが通過する。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_optimizer.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/regenerate_samples.py --langs cpp --stems 18_mini_language_interpreter --force`
- `python3 tools/check_py2cpp_transpile.py`

分解:
- [x] [ID: P0-EAST3-RESERVE-COUNT-NORM-01-S1-01] `reserve_hints` 拡張仕様（`count_expr` 形式 / fail-closed 条件 / 互換扱い）を定義する。
- [x] [ID: P0-EAST3-RESERVE-COUNT-NORM-01-S1-02] `StaticRange` 件数式の正規化ルール（`start=0,step=1` 等の簡約規則）を仕様化する。
- [ ] [ID: P0-EAST3-RESERVE-COUNT-NORM-01-S2-01] EAST3 optimizer で正規化済み `count_expr` を生成し、`reserve_hints` へ付与する。
- [ ] [ID: P0-EAST3-RESERVE-COUNT-NORM-01-S2-02] C++ emitter を `count_expr` 描画方式へ切り替え、文字列組み立て依存を撤去する。
- [ ] [ID: P0-EAST3-RESERVE-COUNT-NORM-01-S2-03] `count_expr` 欠落/不正時の fail-closed 挙動を実装し、不正 `reserve` 出力を防止する。
- [ ] [ID: P0-EAST3-RESERVE-COUNT-NORM-01-S3-01] unit テスト（optimizer + emitter）を追加し、旧式冗長 `reserve` 式の再発を検知可能にする。
- [ ] [ID: P0-EAST3-RESERVE-COUNT-NORM-01-S3-02] `sample/cpp/18` 再生成と transpile チェックを実行し、非退行を確認する。

決定ログ:
- 2026-03-02: ユーザー指示により、`reserve` 件数式の正規化責務を C++ emitter から EAST3 側へ移す P0 計画を起票。
- 2026-03-02: [ID: P0-EAST3-RESERVE-COUNT-NORM-01-S1-01] `reserve_hints[*].count_expr` を EAST3式ノードで保持する契約と fail-closed 条件を確定した。
- 2026-03-02: [ID: P0-EAST3-RESERVE-COUNT-NORM-01-S1-02] `StaticRange` trip count の正規化ルール（ascending/descending + step簡約）を固定した。

## S1実施結果（2026-03-02）

### S1-01: `reserve_hints` 拡張仕様（`count_expr`）

- 追加キー:
  - `reserve_hints[*].count_expr`: EAST3式ノード（`Constant/Name/BinOp/Compare/IfExp` の最小部分集合）で trip count を保持する。
  - `reserve_hints[*].count_expr_version`: 文字列 `"east3_expr_v1"`。
- 互換扱い:
  - 既存 `count_kind` は残しつつ、emitter は `count_expr` 優先で読む。
  - `count_expr` 欠落時は `reserve` を出力しない（fail-closed）。旧文字列組み立てへ戻さない。
- fail-closed 条件:
  - `count_expr` が dict でない / `kind` 不正 / 必須子ノード欠落 / 未対応演算子を含む場合は `reserve` 出力を抑止する。
  - `safe != true` / `owner` 空 / hint kind 不一致でも同様に抑止。

### S1-02: `StaticRange` 件数式正規化ルール

- 前提:
  - 適用対象は既存仕様どおり「無条件 append + `StaticRangeForPlan` + 安全判定成立」のみ。
- 正規化:
  - `step == 0` は不正として `count_expr` 生成なし。
  - `range_mode=ascending`:
    - `step_abs == 1`: `stop <= start ? 0 : stop - start`
    - `step_abs > 1`: `stop <= start ? 0 : (stop - start + (step_abs - 1)) / step_abs`
  - `range_mode=descending`:
    - `step_abs == 1`: `stop >= start ? 0 : start - stop`
    - `step_abs > 1`: `stop >= start ? 0 : (start - stop + (step_abs - 1)) / step_abs`
- 簡約:
  - `start=0` / `step=1` は上式から自然に `stop <= 0 ? 0 : stop` へ簡約。
  - 不要な `- (0)` や過剰括弧は emitter 側描画規則で抑制する。
