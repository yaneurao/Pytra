# エージェント運用ルール（ブートストラップ）

このファイルは最初に読む入口だけを定義します。  
詳細ルールの正本は `docs-jp/spec/spec-codex.md` です。

## 起動時に読む順序

1. `docs-jp/spec/index.md`
2. `docs-jp/spec/spec-codex.md`
3. `docs-jp/todo.md`

## 最小ルール

- `docs-jp/` を正本（source of truth）とし、`docs/` は翻訳ミラーとして扱う。
- `docs-jp/` 直下（トップレベル）への新規ファイル追加は原則禁止（同一ターンの明示依頼がある場合のみ許可）。
- `docs-jp/plans/`、`docs-jp/language/`、`docs-jp/todo-history/`、`docs-jp/spec/` 配下は、運用ルールに沿う範囲で作成可。

## 参照先

- Codex 運用ルール本体: `docs-jp/spec/spec-codex.md`
- TODO 運用: `docs-jp/todo.md`
- TODO 履歴: `docs-jp/todo-history/index.md`
