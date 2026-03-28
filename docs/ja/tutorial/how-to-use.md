<a href="../../en/tutorial/how-to-use.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# 使い方

Pytra を実際に動かすための実行手順ガイドです。

## まずこの 1 ファイルを動かす

`add.py`:

```python
def add(a: int, b: int) -> int:
    return a + b

if __name__ == "__main__":
    print(add(3, 4))
```

C++ に変換して、build + run する最短手順:

```bash
./pytra add.py --output-dir out/add_case --build --run --exe add.out
```

出力:

```text
7
```

変換結果だけを見たいなら:

```bash
./pytra add.py --output-dir out/add_case
```

Rust に変換するなら `--target` を変えるだけ:

```bash
./pytra add.py --target rs --output-dir out/rs_case
```

## 対応言語

`--target` で指定できる言語:

`cpp`, `rs`, `cs`, `js`, `ts`, `go`, `java`, `kotlin`, `swift`, `ruby`, `lua`, `scala`, `php`, `nim`, `dart`, `julia`, `zig`

全言語で multi-file 出力（`--output-dir`）が正規パスです。

## 主なオプション

| オプション | 説明 |
|---|---|
| `--target <lang>` | 出力言語（既定: `cpp`） |
| `--output-dir <dir>` | 出力ディレクトリ（既定: `out/`） |
| `--build` | C++ のみ。変換後にコンパイル |
| `--run` | `--build` と併用。コンパイル後に実行 |
| `--exe <name>` | 実行ファイル名（`--output-dir` 配下に生成） |
| `--help` | ヘルプ表示 |

## 入力コードの制約

Pytra は Python のサブセットを変換します。主な制約:

- **型注釈を書く**: 関数の引数・戻り値には型注釈が必須です。
- **`pytra.std.*` を使う**: Python 標準ライブラリは直接 import できません。代わりに `pytra.std.*` の shim を使います。
  ```python
  from pytra.std import math        # math.sqrt() 等
  from pytra.std.time import perf_counter
  from pytra.std.pathlib import Path
  ```
- **`typing` と `dataclasses` は例外**: 注釈・decorator 専用として直接 import できます。
- **`if __name__ == "__main__":` を書く**: エントリポイントとして必要です。

詳細は [Python 互換性ガイド](../spec/spec-python-compat.md) を参照してください。
サポート済みモジュール一覧は [pylib モジュール一覧](../spec/spec-pylib-modules.md) を参照してください。

## もう少し大きな例

`sample/py/` に 18 件のサンプルがあります。Mandelbrot 集合、レイトレーシング、ゲームオブライフ等の実用的なプログラムです。

```bash
# sample を C++ で変換 + build + run
./pytra sample/py/01_mandelbrot.py --output-dir out/mandelbrot --build --run --exe mandelbrot.out
```

## 次に読むページ

1. [エラーの見方](./troubleshooting.md) — 詰まったときに
2. [例外処理](./exception.md) — raise / try / except / finally の使い方
3. [Trait（インターフェース）](./trait.md) — 複数の振る舞い契約を型に付与する
4. [Union 型と isinstance ナローイング](./union-and-narrowing.md) — 複数の型を扱う方法と型の自動絞り込み
5. [Python 互換性ガイド](../spec/spec-python-compat.md) — Python との違い、使えない構文

ここから先は必要に応じて:

6. [アーキテクチャ](./architecture.md) — パイプラインの全体像と各段の役割
7. [発展的な使い方](./advanced-usage.md) — `@extern`, `@abi`, `@template`, nominal ADT 等
8. [仕様書トップ](../spec/index.md) — 言語仕様の正本
9. [開発運用ガイド](./dev-operations.md) — parity check, local CI（開発者向け）
