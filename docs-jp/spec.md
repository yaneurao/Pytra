# 仕様書（入口）

<a href="../docs/spec.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>


`docs-jp/spec.md` は仕様全体の入口ページです。詳細は次の3ファイルに分割しています。

- 利用仕様: [利用仕様](./spec/spec-user.md)
- 実装仕様: [実装仕様](./spec/spec-dev.md)
- ランタイム仕様: [ランタイム仕様](./spec/spec-runtime.md)
- GC 仕様: [GC 仕様](./spec/spec-gc.md)
- 言語プロファイル仕様: [言語プロファイル仕様](./spec/spec-language-profile.md)
- 言語別仕様: [言語別仕様](./language/index.md)
- Codex 向け運用仕様: [Codex 向け運用仕様](./spec-codex.md)
- `pylib` モジュール一覧: [pylib モジュール一覧](./pylib-modules.md)

## 読み分け方

- ツールの使い方・入力制約・テスト実行方法を確認したい場合:
  - [利用仕様](./spec/spec-user.md)
- 実装方針・モジュール構成・変換仕様を確認したい場合:
  - [実装仕様](./spec/spec-dev.md)
- C++ ランタイム配置・include対応規約を確認したい場合:
  - [ランタイム仕様](./spec/spec-runtime.md)
- RC ベースの GC 方針を確認したい場合:
  - [GC 仕様](./spec/spec-gc.md)
- `CodeEmitter` の JSON プロファイルと hooks 仕様を確認したい場合:
  - [言語プロファイル仕様](./spec/spec-language-profile.md)
- 言語ごとの機能対応状況を確認したい場合:
  - [言語別仕様](./language/index.md)
- Codex の作業ルール・TODO 運用・コミット運用を確認したい場合:
  - [Codex 向け運用仕様](./spec-codex.md)

## Codex 起動時の確認先

- Codex は起動時に `docs-jp/spec.md` を入口として読み、続けて [Codex 向け運用仕様](./spec-codex.md) と [TODO](./todo.md) を確認します。

## Any の現行方針

- `Any` は C++ では `object`（`rc<PyObj>`）として表現します。
- `None` は `object{}`（null ハンドル）で表現します。
- boxing/unboxing は `make_object(...)` / `obj_to_*` / `py_to_*` を使用します。
