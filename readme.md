# Pytraとは何？

Pytraは、Pythonのサブセットで書かれたプログラムを様々な言語に変換するためのトランスパイラ群です。

現在は Python から C++/C# への変換に対応しており、JavaScript/TypeScript/Rust/Go/Java/Swift/Kotlin は対応予定です。

⚠ まだ開発途上にあり、実用にほど遠いかもしれません。サンプルコードなどを確認してから自己責任において、ご利用ください。
⚠ Pythonで書いたプログラムを丸ごと移植できることは期待しないでください。「Pythonで書いたコアコードが上手く変換されたらラッキーだな」ぐらいの温度感でお使いください。

## 開発動機

マルチプラットフォーム対応のゲームを作ろうと思うと、現在は、Unityが現実解です。UnityではC#で書く必要があります。私はサーバーサイドは、Pythonで書きたかったのですが、ブラウザ側もあるなら、そこはJavaScriptで書く必要があります。

こうなると3つの言語を行き来することになります。場合によっては同じロジックを3回実装しなければなりません。これはさすがにおかしいのではないか？と思ったのが開発のきっかけです。

また、素のPythonだと遅すぎてサーバーサイドで大量のリクエストを捌くのには向かないです。ここが少しでも速くなればと思い、開発しました。

JavaScriptのコードにも変換できるので、Pythonでブラウザゲームの開発もできます。

## 使い方について

実際の使い方については [docs/how-to-use.md](docs/how-to-use.md) をご覧ください。


## 実行速度の比較

サンプルコード(Pythonで書かれている)の実行時間と、そのトランスパイルしたソースコードでの実行時間。（単位: 秒）

💡 元のソースコード、変換されたソースコード、計測条件等については、[docs/time-comparison.md](docs/time-comparison.md) をご覧ください。

|ファイル名|内容|Python| C++ | C# | JS | Rust |
|-|-|-:|-:|-:|-|-|
|01_mandelbrot|マンデルブロ集合（PNG）|1.689|0.089|0.078|🚧|🚧|
|02_raytrace_spheres|球の簡易レイトレーサ（PNG）|0.414|0.030|0.121|🚧|🚧|
|03_julia_set|ジュリア集合（PNG）|1.380|0.087|0.141|🚧|🚧|
|04_monte_carlo_pi|モンテカルロ法で円周率近似|3.657|0.052|0.200|🚧|🚧|
|05_mandelbrot_zoom|マンデルブロズーム（GIF）|13.802|0.525|2.694|🚧|🚧|
|06_julia_parameter_sweep|ジュリア集合パラメータ掃引（GIF）|5.724|0.234|0.190|🚧|🚧|
|07_game_of_life_loop|ライフゲーム（GIF）|1.290|0.067|0.314|🚧|🚧|
|08_langtons_ant|ラングトンのアリ（GIF）|0.744|0.050|0.234|🚧|🚧|
|09_fire_simulation|炎シミュレーション（GIF）|1.088|0.054|0.522|🚧|🚧|
|10_plasma_effect|プラズマエフェクト（GIF）|2.419|0.221|0.769|🚧|🚧|
|11_lissajous_particles|リサージュ粒子（GIF）|1.118|0.081|0.163|🚧|🚧|
|12_sort_visualizer|ソート可視化（GIF）|3.471|0.233|0.465|🚧|🚧|
|13_maze_generation_steps|迷路生成ステップ（GIF）|0.521|0.033|0.113|🚧|🚧|
|14_raymarching_light_cycle|簡易レイマーチング（GIF）|2.666|0.152|0.467|🚧|🚧|
|15_mini_language_interpreter|ミニ言語インタプリタ |2.207|0.577|1.035|🚧|🚧|

## 実装済みの言語機能

- 変数代入（通常代入、型注釈付き代入、拡張代入の主要ケース）
- 算術演算（`+ - * / // % **` の主要ケース）
- 比較演算（`== != < <= > >= in not in is is not` の主要ケース）
- 条件分岐（`if / elif / else`）
- ループ（`while`、`for in <iterable>`、`for in range(...)`）
- 例外（`try/except/finally`、`raise` の主要ケース）
- 関数定義・関数呼び出し・戻り値
- クラス定義（単一継承、`__init__`、static member、instance member）
- `@dataclass` の基本変換
- 文字列（f-string の主要ケース、`replace` などの主要メソッド）
- コンテナ（`list`, `dict`, `set`, `tuple` の主要ケース）
- list/set comprehension の主要ケース
- `if __name__ == "__main__":` ガードの認識
- 型マッピング（`int`, `int8..uint64`, `float`, `float32`, `str`, `bool`, `None`）
- a[b:c] 形式のスライス構文

### module

- `math`（主要関数: `sqrt`, `sin`, `cos`, `tan`, `exp`, `log`, `log10`, `floor`, `ceil`, `pow` など）
- `time`（`perf_counter`）
- `pathlib`（利用中機能の範囲）
- `dataclasses`（`@dataclass`）
- `ast`（セルフホスティングのためのランタイム実装）

独自追加。
- `py_module.png_helper` : PNG画像出力ヘルパ
- `py_module.gif_helper` : GIF画像出力ヘルパ

## 開発中

- C++, C#以外の言語へのトランスパイラ本体
- a[b:c] 以外のスライス構文

## 未実装項目

- 標準ライブラリ網羅対応（`import` 可能モジュールの拡充）
- 例外処理・型推論の高度化

## 対応予定なし

- Python 構文の完全互換（現状はサブセット）
- 動的なimport
- 動的な型付け
- 弱参照, 循環参照 非対応
- スライスオブジェクト


## 開発について

本トランスパイラは、主にGPT-5.3-Codexで開発しています。

## ライセンス

MIT License
