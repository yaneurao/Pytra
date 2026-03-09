# チュートリアル

Pytra を初めて触る人向けの入口です。  
まずはここから読み進めてください。

## 最初に読む順番

1. 実行手順を確認する: [使い方](./how-to-use.md)
2. 言語仕様の正本を確認する: [利用仕様](../spec/spec-user.md)
3. `@extern` / `extern(...)` を確認する: [extern.md](./extern.md)
4. `py2x.py` / `ir2lang.py` を直接使う: [transpiler-cli.md](./transpiler-cli.md)
5. エラーの見方と詰まりどころを確認する: [troubleshooting.md](./troubleshooting.md)
6. 高度な変換ルートを確認する: [発展的な使い方](./advanced-usage.md)
7. parity / selfhost / local CI を確認する: [開発運用ガイド](./dev-operations.md)

## 読み分け

- `.py` を各ターゲット言語へ変換して実行したい
  - [使い方](./how-to-use.md)
- `@extern` / `extern(...)` を使いたい
  - [extern.md](./extern.md)
- `py2x.py` / `ir2lang.py` を直接使いたい
  - [transpiler-cli.md](./transpiler-cli.md)
- エラーカテゴリや詰まりどころを確認したい
  - [troubleshooting.md](./troubleshooting.md)
- `@abi` や linked-program route を使いたい
  - [発展的な使い方](./advanced-usage.md)
- parity や selfhost を含む開発運用を確認したい
  - [開発運用ガイド](./dev-operations.md)
- 仕様の正本を確認したい
  - [仕様書トップ](../spec/index.md)

## 関連リンク

- 利用仕様: [spec-user.md](../spec/spec-user.md)
- オプション仕様: [spec-options.md](../spec/spec-options.md)
- ツール一覧: [spec-tools.md](../spec/spec-tools.md)
