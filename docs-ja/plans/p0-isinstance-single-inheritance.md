# P0 type_id 単一継承範囲判定リフォーマット

関連 TODO:
- `docs-ja/todo/index.md` の `ID: P0-ISINSTANCE-01`

背景:
- `spec-type_id.md` を単一継承＋`type_id_min/max`で統一する方向に更新したが、`isinstance` の実装は言語別に残渣があり、実運用上の分岐が温存されている。
- 既存の `P0-SAMPLE-GOLDEN-ALL-01` では全言語ゴールデン整合が最終目標だが、`isinstance` が不統一だと最終到達まで再修正が連鎖しやすい。
- まず `isinstance` 判定を `type_id` 区間判定へ強制的に一本化し、複数の emitter で同じ意味論へ揃える。

対象:
- `isinstance` 判定を使用している emitter 出力（最低限 C++ / JS / TS / Rust / C#）
- `type_id` API 呼び出し導線（`py_isinstance` / `py_is_subtype` / `py_issubclass`）の利用
- 既存の多重継承前提ロジック、文字列名依存比較、例外的 built-in パス

非対象:
- ABC/virtual subclass の再現
- 全ターゲット同時一括移行（段階移行可）

受け入れ基準:
- `isinstance(x, T)` がすべての対象ターゲットで `type_id_min/max` を使った区間判定へ統一される。
- 多重継承指定（複数基底）はエラー扱いへ明確化する。
- `tools/` 系 smoke/回帰テストで `isinstance` 系の既存ケースが green になる。
- `docs-ja/spec/spec-type_id.md` の区間判定定義と矛盾しない。

子タスク:
- `P0-ISINSTANCE-01-S1`: 仕様と現状照合（対象 emitter/runtime の `isinstance` lower を棚卸し）。
- `P0-ISINSTANCE-01-S2`: C++ runtime/emit 経路を `py_isinstance` API 化し、`type_id` 範囲判定へ置換。
- `P0-ISINSTANCE-01-S3`: JS/TS/RS/CS runtime と lower を `py_type_id` API へ集約。
- `P0-ISINSTANCE-01-S4`: テスト再整理（`test/unit/*isinstance*`）と `check_todo` との対応。
- `P0-ISINSTANCE-01-S5`: 仕様整合ログを `docs-ja/spec/spec-type_id.md` へ反映し、必要なら `spec-boxing` / `spec-linker` の交差条件追記。

決定ログ:
- 2026-02-25: `type_id` を単一継承区間判定へ変更したため、実装側の最優先タスクを追加。`isinstance` 以外の runtime 判定と混在しない実装方針を採用。
