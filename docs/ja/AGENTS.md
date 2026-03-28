<a href="../en/AGENTS.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# エージェント運用ルール（ブートストラップ）

このファイルは最初に読む入口だけを定義します。  
詳細ルールの正本は `docs/ja/spec/spec-agent.md` です。

## 起動時に読む順序

1. `docs/ja/spec/index.md`
2. `docs/ja/spec/spec-agent.md`
3. `docs/ja/todo/index.md`

## 最小ルール

- `docs/ja/` を正本（source of truth）とし、`docs/en/` は翻訳ミラーとして扱う。
- `docs/ja/` 直下（トップレベル）への新規ファイル追加は原則禁止（同一ターンの明示依頼がある場合のみ許可）。
- `docs/ja/plans/`、`docs/ja/language/`、`docs/ja/todo/archive/`、`docs/ja/spec/` 配下は、運用ルールに沿う範囲で作成可。
- 作業生成物は `work/tmp/` を使用する。selfhost テストは `work/selfhost/` を使用する。
- **以下への出力は禁止**: `out/`, `selfhost/`, `sample/obj/`, `/tmp/`。
- `sample/out/` は sample/py の出力見本（PNG/GIF/TXT）専用。それ以外の用途での出力禁止。
- リポジトリ直下に一時出力ディレクトリを作成してはならない。
- `materials/` はユーザー資料置き場として扱い、Codex は read-only（明示指示がある場合のみ編集可）。
- `materials/Yanesdk/` と `materials/microgpt/` はユーザー管理資料として扱う。
- 変換互換性テストの原本（例: `materials/microgpt/microgpt-20260222.py`）は改変禁止とし、変換器都合の回避版が必要な場合は `work/tmp/*-lite.py` を別名で作成して分離する。

## git 操作の禁止事項（複数インスタンス環境）

複数の Codex / Claude Code インスタンスが同一ワーキングツリーで同時に動作する。以下を厳守すること。

- **`git stash` / `git checkout -- <file>` / `git restore` / `git reset --hard` / `git clean -f` は禁止**。他インスタンスの未コミット変更を破壊する。
- **`.git/index.lock` を削除してはならない**。このファイルが存在するときは他のインスタンスが git 操作中である。削除すると index が壊れる。ロックが残っている場合は **待つ**こと。
- 変更を取り消したい場合は、Edit/Write で手動で元に戻すか、`git diff <file>` で差分を確認してから対処する。

## TODO 起票のルール

- **新機能の導入タスクには、旧機能の撤去タスクも必ずセットで含めること**。新しい仕組みを入れるだけで旧い仕組みの撤去を忘れると、旧コードが残り続けて二重管理やバグの原因になる。

## golden / テスト生成の禁止事項

- **golden ファイル（east1/east2/east3/east3-opt/linked）は `python3 tools/regenerate_golden.py` でのみ生成すること**。`pytra-cli2` を直接叩いて手動で出力先を指定してはならない。手動生成はパスの間違い（`test/fixtures/` や `test/pytra/east1/built_in/` のような誤ったディレクトリ）の原因になる。
- **sample の再生成は `python3 tools/regenerate_samples.py` でのみ行うこと**。
- **`test/fixture/` 配下のディレクトリ構造を勝手に作らないこと**。既存のディレクトリ構成（`source/py/`, `east1/py/`, `east2/`, `east3/`, `east3-opt/`, `linked/`）に従う。
- **`test/` 直下に新しいサブディレクトリを作らないこと**（`test/fixtures/` のような typo ディレクトリを防ぐ）。

## 参照先

- エージェント運用ルール本体: `docs/ja/spec/spec-agent.md`
- TODO 運用: `docs/ja/todo/index.md`
- TODO 履歴: `docs/ja/todo/archive/index.md`
