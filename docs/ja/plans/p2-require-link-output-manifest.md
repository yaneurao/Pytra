<a href="../../en/plans/p2-require-link-output-manifest.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P2: backend に link-output manifest 入力を必須化

最終更新: 2026-03-21

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P2-REQUIRE-LINK-MANIFEST`

## 背景

`loader.py` の `load_linked_modules` は、入力が link-output manifest でない場合に raw EAST3 JSON をフォールバックとして受け付ける（line 31-33）。

この挙動により、`import pytra.std.json` 等の依存モジュールが linker で解決されず、コード生成時に欠落する。全 non-C++ backend が `emit_all_modules` 経由でこの `load_linked_modules` を使っているため、問題は全 backend に共通。

## 対象

| ファイル | 変更内容 |
|---|---|
| `src/toolchain/emit/loader.py` | `load_linked_modules` の raw EAST3 フォールバックを除去し、schema 不一致時にエラーにする |

## 非対象

- C++ backend（`cpp/cli.py` で独自の multi-module パスを持ち、`emit_all_modules` を使っていない）
- linker 側の link-output 生成ロジック

## 受け入れ基準

- [x] `load_linked_modules` が raw EAST3 JSON を受け取った場合にエラーを返す
- [x] 既存の link-output manifest 経由の emit パスがリグレッションしない

## 子タスク

- [x] [ID: P2-REQUIRE-LINK-MANIFEST-01] `loader.py` の raw EAST3 フォールバックを除去する

## 決定ログ

- 2026-03-21: import モジュール解決の調査中に、全 non-C++ backend が raw EAST3 をフォールバック受け付けしており、依存モジュールのリンクが欠落する問題を確認。link-output manifest 必須化を起票。
