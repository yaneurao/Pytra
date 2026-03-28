<a href="../../en/tutorial/README.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# チュートリアル

Pytra を初めて触る人向けの入口です。

## 3分で動かす

```python
def add(a: int, b: int) -> int:
    return a + b

if __name__ == "__main__":
    print(add(3, 4))
```

この `add.py` を C++ に変換して実行:

```bash
./pytra add.py --output-dir out/add_case --build --run --exe add.out
```

出力:

```text
7
```

Rust に変換するなら:

```bash
./pytra add.py --target rs --output-dir out/rs_case
```

## 読む順番

1. [使い方](./how-to-use.md) — 実行手順、オプション、入力制約
2. [エラーの見方](./troubleshooting.md) — 詰まったときに
3. [サンプルを動かしてみる](./samples.md) — 18 件のサンプルプログラムで試す
4. [例外処理](./exception.md) — raise / try / except / finally の使い方
5. [Trait（インターフェース）](./trait.md) — 複数の振る舞い契約を型に付与する
6. [Union 型と isinstance ナローイング](./union-and-narrowing.md) — 複数の型を扱う方法と型の自動絞り込み
7. [Python 互換性ガイド](../spec/spec-python-compat.md) — Python との違い、使えない構文

ここまで読めば普通に使えます。以下は必要に応じて:

8. [pylib モジュール一覧](../spec/spec-pylib-modules.md) — 使えるモジュールと関数の一覧
9. [アーキテクチャ](./architecture.md) — パイプラインの全体像と各段の役割
10. [発展的な使い方](./advanced-usage.md) — `@extern`, `@abi`, `@template`, nominal ADT 等
11. [仕様書トップ](../spec/index.md) — 言語仕様の正本
12. [開発運用ガイド](./dev-operations.md) — parity check, local CI（開発者向け）
