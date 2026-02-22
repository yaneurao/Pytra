# 仕様書（入口）

<a href="../../docs/spec/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>


`docs-jp/spec/index.md` は仕様全体の入口ページです。詳細は次の3ファイルに分割しています。

- 利用仕様: [利用仕様](./spec-user.md)
- 実装仕様: [実装仕様](./spec-dev.md)
- ランタイム仕様: [ランタイム仕様](./spec-runtime.md)
- Boxing/Unboxing 仕様: [Boxing/Unboxing 仕様](./spec-boxing.md)
- GC 仕様: [GC 仕様](./spec-gc.md)
- 言語プロファイル仕様: [言語プロファイル仕様](./spec-language-profile.md)
- 言語別仕様: [言語別仕様](../language/index.md)
- Codex 向け運用仕様: [Codex 向け運用仕様](./spec-codex.md)
- `pylib` モジュール一覧: [pylib モジュール一覧](./spec-pylib-modules.md)
- 開発思想: [開発思想](./spec-philosophy.md)

## 読み分け方

- ツールの使い方・入力制約・テスト実行方法を確認したい場合:
  - [利用仕様](./spec-user.md)
- 実装方針・モジュール構成・変換仕様を確認したい場合:
  - [実装仕様](./spec-dev.md)
- C++ ランタイム配置・include対応規約・`Any` の C++ 表現方針を確認したい場合:
  - [ランタイム仕様](./spec-runtime.md)
- `Any/object` 境界の Boxing/Unboxing 契約を確認したい場合:
  - [Boxing/Unboxing 仕様](./spec-boxing.md)
- RC ベースの GC 方針を確認したい場合:
  - [GC 仕様](./spec-gc.md)
- `CodeEmitter` の JSON プロファイルと hooks 仕様を確認したい場合:
  - [言語プロファイル仕様](./spec-language-profile.md)
- 言語ごとの機能対応状況を確認したい場合:
  - [言語別仕様](../language/index.md)
- Codex の作業ルール・TODO 運用・コミット運用を確認したい場合:
  - [Codex 向け運用仕様](./spec-codex.md)
- 設計思想・EAST 中心設計の背景を確認したい場合:
  - [開発思想](./spec-philosophy.md)

## Codex 起動時の確認先

- Codex は起動時に `docs-jp/spec/index.md` を入口として読み、続けて [Codex 向け運用仕様](./spec-codex.md) と [TODO](../todo.md) を確認します。
