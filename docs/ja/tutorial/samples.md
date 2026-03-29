<a href="../../en/tutorial/samples.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# サンプルを動かしてみる

Pytra には 18 件のサンプルプログラムが付属しています。フラクタル画像、レイトレーシング、ゲームオブライフ、ソートの可視化、ミニ言語インタプリタなど、実用的なプログラムが揃っています。

## まず 1 つ動かす

マンデルブロ集合を C++ に変換して実行:

```bash
./pytra sample/py/01_mandelbrot.py --output-dir out/mandelbrot --build --run --exe mandelbrot.out
```

PNG 画像が生成されます。

Go に変換するなら:

```bash
./pytra sample/py/01_mandelbrot.py --target go --output-dir out/mandelbrot_go
```

## サンプル一覧

| No | 内容 | 出力 |
|---|---|---|
| 01 | マンデルブロ集合 | PNG |
| 02 | レイトレーシング（球体） | PNG |
| 03 | ジュリア集合 | PNG |
| 04 | オービットトラップ・ジュリア | PNG |
| 05 | マンデルブロズーム | GIF |
| 06 | ジュリア集合パラメータ掃引 | GIF |
| 07 | ゲームオブライフ | GIF |
| 08 | ラングトンのアリ | GIF |
| 09 | 火災シミュレーション | GIF |
| 10 | プラズマエフェクト | GIF |
| 11 | リサジュー粒子 | GIF |
| 12 | ソート可視化 | GIF |
| 13 | 迷路生成 | GIF |
| 14 | レイマーチング・ライトサイクル | GIF |
| 15 | 波の干渉 | GIF |
| 16 | ガラス彫刻のカオス回転 | GIF |
| 17 | モンテカルロ法による円周率 | テキスト |
| 18 | ミニ言語インタプリタ | テキスト |

出力例:

<table><tr>
<td width="50%">

![01_mandelbrot](../../../sample/images/01_mandelbrot.png)

01: マンデルブロ集合

</td>
<td width="50%">

![07_game_of_life_loop](../../../sample/images/07_game_of_life_loop.gif)

07: ゲームオブライフ

</td>
</tr></table>

## 変換後のコードを見る

Python のソースと変換後のコードを見比べてみましょう。

```bash
# Python のソース
cat sample/py/01_mandelbrot.py

# C++ に変換した結果
cat sample/cpp/01_mandelbrot.cpp

# Go に変換した結果
cat sample/go/01_mandelbrot.go
```

元の Python コードの構造がほぼそのまま残っていることが確認できます。

## 全サンプルを一括変換する

```bash
python3 tools/gen/regenerate_samples.py
```

全 18 件を全言語（18 言語）に変換します。

## 実行速度の比較

Python で実行した場合と、C++/Rust に変換して実行した場合の速度比較:

| No | 内容 | Python | C++ | 倍率 |
|---|---|---|---|---|
| 06 | ジュリア集合パラメータ掃引 | 9.6 秒 | 0.5 秒 | 約 19x |
| 16 | ガラス彫刻のカオス回転 | 6.8 秒 | 0.3 秒 | 約 23x |

全言語・全サンプルの詳細は [サンプル一覧（詳細版）](../../../sample/README-ja.md) を参照してください。

## ソースコード

全サンプルの Python ソースは `sample/py/` にあります。各言語への変換結果は `sample/cpp/`, `sample/go/`, `sample/rs/` 等にあります。

## 関連する仕様

- [利用仕様](../spec/spec-user.md) — ビルドオプションの詳細
- [使えるモジュール](./modules.md) — サンプルで使われている pytra.std.* の解説
