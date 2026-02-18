# 仕様書（入口）

`docs/spec.md` は仕様全体の入口ページです。詳細は次の3ファイルに分割しています。

- 利用仕様: [`docs/spec-user.md`](./spec-user.md)
- 実装仕様: [`docs/spec-dev.md`](./spec-dev.md)
- 言語プロファイル仕様: [`docs/spec-language-profile.md`](./spec-language-profile.md)
- Codex 向け運用仕様: [`docs/spec-codex.md`](./spec-codex.md)

## 読み分け方

- ツールの使い方・入力制約・テスト実行方法を確認したい場合:
  - [`docs/spec-user.md`](./spec-user.md)
- 実装方針・モジュール構成・変換仕様を確認したい場合:
  - [`docs/spec-dev.md`](./spec-dev.md)
- `CodeEmitter` の JSON プロファイルと hooks 仕様を確認したい場合:
  - [`docs/spec-language-profile.md`](./spec-language-profile.md)
- Codex の作業ルール・TODO 運用・コミット運用を確認したい場合:
  - [`docs/spec-codex.md`](./spec-codex.md)

## Codex 起動時の確認先

- Codex は起動時に `docs/spec.md` を入口として読み、続けて [`docs/spec-codex.md`](./spec-codex.md) と [`docs/todo.md`](./todo.md) を確認します。

## Any の現行方針

- `Any` は C++ では `object`（`rc<PyObj>`）として表現します。
- `None` は `object{}`（null ハンドル）で表現します。
- boxing/unboxing は `make_object(...)` / `obj_to_*` / `py_to_*` を使用します。
