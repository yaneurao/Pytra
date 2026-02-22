# エージェント運用ルール

## docs-jp の基本方針

- 作業開始時に `docs-jp/spec-codex.md` を読み、記載ルールに従う。
- `docs-jp/` を正（source of truth）とし、`docs/` は翻訳ミラーとして扱う。
- `docs-jp/` 直下（トップレベル）に新規ファイルを作成することは禁止し、必要時は同一ターンでの明示依頼があるときのみ許可する。
- 例外として `docs-jp/plans/`、`docs-jp/language/`、`docs-jp/todo-history/`、`docs-jp/spec/` 配下は、既存運用ルールに沿う範囲で Codex が自律的に新規ファイルを作成してよい。
- 未完了タスクは `docs-jp/todo.md` にのみ記載する。
- 完了済みは `docs-jp/todo-history/index.md` と `docs-jp/todo-history/YYYYMMDD.md` へ移す。
- 優先度上書きは `docs-jp/todo2.md` ではなくチャット指示で行う（形式は `docs-jp/plans/instruction-template.md`）。

## 長期計画メモの置き場

- 長期計画・設計ドラフト・調査メモは `docs-jp/plans/` に保存する。
- `docs-jp/plans/` の内容は日本語で記述する。
- 実行可能な未完了タスクに落ちた項目だけを `docs-jp/todo.md` に転記する。

## タスク文脈保持ルール

- `docs-jp/todo.md` の各タスクは、`[ID: ...]` と対応 plan ファイル参照を必須にする。
- 着手前に対応 plan の `背景` / `非対象` / `受け入れ基準` を確認し、作業開始時に要点を再確認する。
- 作業中に判断した内容は、対応 plan の `決定ログ` に日付付きで追記する。
- 完了移管時（`todo-history/index.md` / `todo-history/YYYYMMDD.md`）は、対応 ID と根拠（コミット、確認コマンド）を残す。

## ガード運用

- docs を触ったコミット前に `python3 tools/check_docs_jp_guard.py` を実行する。
- `tools/check_docs_jp_guard.py` は `docs-jp/` 配下の未管理ファイルを検出したら失敗する。

## 生成物 `out/` 運用

- `out/` はローカル検証用の一時生成物ディレクトリとして扱い、Git 管理しない。
- `out/` には再生成可能な成果物のみを置き、唯一の正本を置かない。
- コミット前に `out/` 配下の変更をステージしない。

## 対外リリース版バージョン運用

- 対外リリース版の正本はリポジトリ直下 `VERSION` とし、形式は `MAJOR.MINOR.PATCH`（SemVer）とする。
- 現在の対外リリース版は `0.0.1` とする。
- `PATCH` のインクリメントは Codex が実施してよい。
- `MAJOR` / `MINOR` のインクリメントはユーザーの明示指示がある場合のみ実施する。
- 内部運用用の `src/pytra/compiler/transpiler_versions.json` は、対外リリース版とは別管理とする。
