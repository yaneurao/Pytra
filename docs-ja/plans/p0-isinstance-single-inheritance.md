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

現状棚卸し（2026-02-25）:
- `C++`: emitter lower は `py_isinstance` / `py_is_subtype` / `py_issubclass` 呼び出しを利用しているが、`type_id` 実体（`src/pytra/built_in/type_id.py`）はまだ基底グラフ走査。
- `JS/TS`: `isinstance` は `pyIsInstance` に lower 済み。runtime は `pyTypeId` + 基底グラフ（`Map<typeId, bases[]>`）で判定しており、区間判定への置換が未実施。
- `Rust`: emitter が `resolved_type` と `class_base_map` を直接参照して `isinstance` を式展開しており、runtime API 経由の判定に未統一。
- `C#`: emitter が `is` 判定へ直接 lower しており、`type_id` runtime API への統一が未実施。
- `self_hosted parser`: 複数基底クラス（`class C(A, B):`）は従来 generic な parse 失敗だったため、今回 `multiple inheritance is not supported` の明示エラーへ変更。

決定ログ:
- 2026-02-25: `type_id` を単一継承区間判定へ変更したため、実装側の最優先タスクを追加。`isinstance` 以外の runtime 判定と混在しない実装方針を採用。
- 2026-02-25: `P0-ISINSTANCE-01` `self_hosted` パーサで複数基底クラスを明示エラー化し、`isinstance` lower の棚卸し結果（C++/JS/TS/RS/CS）を記録した。
- 2026-02-25: `P0-ISINSTANCE-01` `src/pytra/built_in/type_id.py` と JS/TS runtime の `py_is_subtype` を区間判定（order/min/max）へ切替え、sibling 系の誤包含を防ぐ回帰テストを追加した。
- 2026-02-25: `P0-ISINSTANCE-01` C# emitter の `isinstance` lower を `Pytra.CsModule.py_runtime.py_isinstance` 呼び出しへ統一し、runtime に `PYTRA_TID_*` / `py_runtime_type_id` / `py_is_subtype` / `py_isinstance` を追加した。
