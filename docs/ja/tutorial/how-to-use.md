# 使い方について

<a href="../../en/how-to-use.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>


このドキュメントは、Pytra を実際に動かすための実行手順ガイドです。
入力制約や言語仕様の正本は [仕様書トップ](../spec/index.md) を参照してください。
型推論の詳細は [EAST仕様の型推論ルール](../spec/spec-east.md#7-型推論ルール) にあります。

## まずこの 1 ファイルを動かす

最初は fixture を読むより、自分で最小例を 1 本動かすほうが早いです。

`add.py`:

```python
def add(a: int, b: int) -> int:
    return a + b


if __name__ == "__main__":
    print(add(3, 4))
```

これを C++ に変換して、そのまま build + run する最短手順は次です。

```bash
./pytra add.py --output-dir out/add_case --build --run --exe add.out
```

想定される標準出力:

```text
7
```

まず変換結果だけを見たいなら、single-file 出力を使います。

```bash
./pytra add.py --output out/add.cpp
```

Rust に変換したいなら `--target` だけ変えます。

```bash
./pytra add.py --target rs --output out/add.rs
```

このページの後半では `test/fixtures/...` を使ったコマンド例も出てきますが、理解の起点は上の `add.py` を基準にすると楽です。

## 統合CLI（`./pytra`）の使い方

ルートの `./pytra` は、`python3 src/pytra-cli.py` を呼び出す統合CLIランチャーです。

```bash
# ヘルプ
./pytra --help

# C++へ単一ファイル出力
./pytra test/fixtures/core/add.py --output /tmp/add.cpp

# Rustへ単一ファイル出力
./pytra test/fixtures/core/add.py --target rs --output /tmp/add.rs

# C++を複数ファイル出力（manifest付き）
./pytra test/fixtures/core/add.py --output-dir out/add_case

# Rustを out/ 配下へ出力
./pytra test/fixtures/core/add.py --target rs --output-dir out/rs_case

# 変換 + ビルド + 実行
./pytra test/fixtures/core/add.py --build --output-dir out/add_case --exe add.out --run
```

補足:
- `--target` は `cpp` / `rs` に対応しています。
- `--build` は `--target cpp` のみ対応です（Rust は変換のみ）。
- 生成コード最適化レベルは `--codegen-opt {0,1,2,3}` で指定できます。
- `--target cpp --codegen-opt 3` は C++ 向け max Pytra codegen route です。raw `EAST3` -> linked-program optimizer -> backend restart を内部で通します。
- `--opt -O3` は build 時の C++ compiler flag であり、`--codegen-opt 3` とは別です。
- `--target cpp --codegen-opt 3` は multi-file output 前提です。transpile-only では `--output` は使わず、`--output-dir` を指定してください。
- `--build` 時の生成物（`src/*.cpp`, `include/*.h`, `.obj/*.o`, 実行ファイル）は `--output-dir` 配下に出力されます（既定: `out/`）。
- `--exe` は実行ファイル名/出力先です。相対指定（例: `add.out`）は `--output-dir` 配下に生成されます。
- Rust 変換は `--output` 未指定時、`--output-dir/<入力stem>.rs` へ出力されます（例: `out/rs_case/add.rs`）。
- 一時出力は `out/` に集約する運用を推奨し、共有一時確認が必要な場合のみ `/tmp` を使用します。

## 最初に確認する制約

- Python の標準ライブラリ直接 import は原則非推奨です。`pytra.std.*` を使ってください。
- ただし `typing` だけは注釈専用 no-op import として許可します（`import typing` / `from typing import ...` は依存解決に残しません）。
- `dataclasses` も decorator 解決専用 no-op import として許可します（`import dataclasses` / `from dataclasses import ...` は依存解決に残しません）。
- `math` / `random` / `timeit` / `enum` などの実行時利用は `pytra.std.*` 対応 shim に正規化して扱います。
- `import` できるのは `src/pytra/` 配下にあるモジュール（`pytra.std.*`, `pytra.utils.*`, `pytra.compiler.*`）と、ユーザーが作成した自作 `.py` モジュールです。
- 自作モジュール import は仕様上合法ですが、複数ファイル依存解決は段階的に実装中です。
- サポート済みモジュール一覧と API は [モジュール一覧](../spec/spec-pylib-modules.md) を参照してください。
- 変換オプションの方針と候補は [オプション仕様](../spec/spec-options.md) を参照してください。
- 補助スクリプト（`tools/`）の用途一覧は [ツール一覧](../spec/spec-tools.md) を参照してください。
- 制約の根拠と正規仕様は [仕様書トップ](../spec/index.md) を参照してください。

## 次に読むページ

- 言語仕様の入口は [仕様書トップ](../spec/index.md) を参照してください。
- 型推論の詳細は [EAST仕様の型推論ルール](../spec/spec-east.md#7-型推論ルール) を参照してください。
- `@extern` / `extern(...)` の使い方は [extern.md](./extern.md) を参照してください。
- `py2x.py` / `ir2lang.py` を直接使いたい場合は [transpiler-cli.md](./transpiler-cli.md) を参照してください。
- エラーカテゴリや詰まりどころは [troubleshooting.md](./troubleshooting.md) を参照してください。
- 高度な変換ルートや `@abi` は [発展的な使い方](./advanced-usage.md) を参照してください。
- parity / local CI / backend health などの運用手順は [開発運用ガイド](./dev-operations.md) を参照してください。
- CLI オプションの詳細は [オプション仕様](../spec/spec-options.md) を参照してください。
