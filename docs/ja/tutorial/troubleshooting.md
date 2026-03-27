<a href="../../en/tutorial/troubleshooting.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# エラーの見方と詰まりどころ

このページは、Pytra の変換時エラーの見方と、詰まりやすいポイントへの導線をまとめたものです。  
言語仕様の正本は [利用仕様](../spec/spec-user.md) と [仕様書トップ](../spec/index.md) を参照してください。

## エラーカテゴリ

`src/pytra-cli.py --target cpp` の失敗時メッセージは、次のカテゴリで表示されます。

- `[user_syntax_error]`
  - ユーザーコードの文法エラーです。
- `[not_implemented]`
  - まだ実装されていない構文です。
- `[unsupported_by_design]`
  - 言語仕様として非対応の構文です。
- `[internal_error]`
  - トランスパイラ内部エラーです。

## よく詰まるポイント

- Python の標準ライブラリをそのまま import している
  - `pytra.std.*` を優先してください。
  - 参照: [spec-pylib-modules.md](../spec/spec-pylib-modules.md)
- 型注釈が足りず、空の `list` / `dict` などの型が決まらない
  - 参照: [spec-user.md](../spec/spec-user.md)
- 対応していない構文を使っている
  - 参照: [spec-user.md](../spec/spec-user.md)
- `getattr(...)` / `setattr(...)` を使っている
  - 文字列名による動的属性参照・更新は intentionally unsupported です。
  - 具体型の `x.field`、`dict` / JSON オブジェクト、`@extern` の専用 seam を検討してください。
- C++ の細かいサポート状況を確認したい
  - 参照: [py2cpp サポートマトリクス](../language/cpp/spec-support.md)
- import / runtime module の対応範囲を確認したい
  - 参照: [spec-pylib-modules.md](../spec/spec-pylib-modules.md)
- CLI オプションの意味を確認したい
  - 参照: [spec-options.md](../spec/spec-options.md)

## 運用寄りの確認

- parity / selfhost / local CI を確認したい
  - [dev-operations.md](./dev-operations.md)
- `pytra-cli.py` / `east2x.py` を直接叩きたい
  - [transpiler-cli.md](./transpiler-cli.md)
- `@extern` / `extern(...)` を使いたい
  - [extern.md](./extern.md)
