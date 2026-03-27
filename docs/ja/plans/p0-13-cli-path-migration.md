<a href="../../en/plans/p0-13-cli-path-migration.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0-13: テストが旧 src/backends/cpp/cli.py パスを参照している

最終更新: 2026-03-21

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CLI-PATH-MIGRATION-01`

## 背景

toolchain フォルダ構成変更により `src/backends/cpp/cli.py` が
`src/toolchain/emit/cpp/cli.py` に移動したが、以下のテストが旧パスをハードコードしている。

- `test/unit/backends/cpp/test_py2cpp_codegen_issues.py:152`
  `(ROOT / "src" / "backends" / "cpp" / "cli.py").read_text(...)`

## 対象

- `test/unit/backends/cpp/test_py2cpp_codegen_issues.py`

## 受け入れ基準

- [ ] `test_py2cpp_kind_lookup_is_centralized` がパスする

## 子タスク

- [ ] [ID: P0-CLI-PATH-MIGRATION-01] テスト内の旧 cli.py パスを新パスに更新

## 決定ログ

- 2026-03-21: 1 箇所のみ。直接パスを書き換える。
