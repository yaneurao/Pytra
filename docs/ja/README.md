
<a href="../../README.md">
  <img alt="Read in English" src="https://img.shields.io/badge/README-English-2563EB?style=flat-square">
</a>

<p align="center">
  <img src="../images/pytra-code-alchemist-s.png" alt="Pytra Code Alchemist" width="256">
</p>

<div align="center">
    <h1>Pytra</h1>
    <img alt="Python" src="https://img.shields.io/badge/-Python-3776AB?style=flat-square&logo=python&logoColor=white">（subset）は Pytra の入力言語で、Pytra はそのコードを複数のターゲット言語へトランスパイルします。
    <p><a href="#read-the-docs-ja">ドキュメントを読む</a></p>
</div>

<div align="center">
    <img alt="C++" src="https://img.shields.io/badge/-C%2B%2B%C2%A0%C2%A0%C2%A0-00599C?style=flat-square&logo=cplusplus&logoColor=white">
    <img alt="Rust" src="https://img.shields.io/badge/-Rust%C2%A0%C2%A0-F6B73C?style=flat-square&logo=rust&logoColor=black">
    <img alt="C#" src="https://img.shields.io/badge/-C%23%C2%A0%C2%A0%C2%A0%C2%A0-239120?style=flat-square&logo=dotnet&logoColor=white">
    <img alt="JS" src="https://img.shields.io/badge/-JS%C2%A0%C2%A0%C2%A0%C2%A0-F7DF1E?style=flat-square&logo=javascript&logoColor=black">
    <img alt="TS" src="https://img.shields.io/badge/-TS%C2%A0%C2%A0%C2%A0%C2%A0-3178C6?style=flat-square&logo=typescript&logoColor=white">
    <img alt="Dart" src="https://img.shields.io/badge/-Dart%C2%A0%C2%A0-00BFA6?style=flat-square&logo=dart&logoColor=white">
    <img alt="Go" src="https://img.shields.io/badge/-Go%C2%A0%C2%A0%C2%A0%C2%A0-00ADD8?style=flat-square&logo=go&logoColor=white">
    <img alt="Java" src="https://img.shields.io/badge/-Java%C2%A0%C2%A0-ED8B00?style=flat-square&logo=openjdk&logoColor=white">
    <br>
    <img alt="Swift" src="https://img.shields.io/badge/-Swift%C2%A0-F05138?style=flat-square&logo=swift&logoColor=white">
    <img alt="Kotlin" src="https://img.shields.io/badge/-Kotlin-7F52FF?style=flat-square&logo=kotlin&logoColor=white">
    <img alt="Ruby" src="https://img.shields.io/badge/-Ruby%C2%A0%C2%A0-BB1200?style=flat-square&logo=ruby&logoColor=white">
    <img alt="Lua" src="https://img.shields.io/badge/-Lua%C2%A0%C2%A0%C2%A0-4C6EF5?style=flat-square&logo=lua&logoColor=white">
    <img alt="Scala3" src="https://img.shields.io/badge/-Scala3-10B981?style=flat-square&logo=scala&logoColor=white">
    <img alt="PHP" src="https://img.shields.io/badge/-PHP%C2%A0%C2%A0%C2%A0-777BB4?style=flat-square&logo=php&logoColor=white">
    <img alt="Nim" src="https://img.shields.io/badge/-Nim%C2%A0%C2%A0%C2%A0-37775B?style=flat-square&logo=nim&logoColor=white">
    <img alt="Julia" src="https://img.shields.io/badge/-Julia-9558B2?style=flat-square&logo=julia&logoColor=white">
</div>
</div>


## 最新ニュース

> **2026-03-11 | v0.13.0 リリース**<br>
> バージョン 0.13.0 リリース。NES(ファミコン)のエミュレーターをPython + SDL3で書きました。[スーパーマリオ3が動きました。](https://x.com/yaneuraou/status/2031612549658202538) 非常に遅いです。これをPytraでC++に変換できるように、現在Pytra側を改良中です。

> **2026-03-10 | v0.12.0 リリース**<br>
> バージョン 0.12.0 リリース。いま、Runtime整理の大工事中です。

> **2026-03-09 | v0.11.0 リリース**<br>
> バージョン 0.11.0 リリース、object境界を見直し中です。また、チュートリアルを整備しました。

> **2026-03-08 | v0.10.0 リリース**<br>
> バージョン 0.10.0 リリース、`@template` を使えるようになりました。現在、各言語の runtime を整備中です。

- 過去ニュース: [docs/ja/news/index.md](news/index.md)


## 特徴

Pytraの特徴

- Pythonから各言語への変換器
  - C++, C#, Rust, JavaScript, TypeScript, Go, Java, Swift, Kotlin, Ruby, Lua, Scala3, PHP に変換可能。
  - 元のソースコードに極めて近い形のまま変換

- C++で書くのと同等のコードをPythonで書けることが目標
  - intはデフォルトで 64-bit 符号付き整数
  - 動的な型付けなし

- シンプルな言語仕様
  - 基本的にPythonのサブセット
  - VS Code など既存ツールで開発できる
  - 多重継承を廃して、単純継承のみ

- 高い拡張性
  - トランスパイラ本体も Python で実装しており、拡張・改造しやすい構成
  - トランスパイラ自身のソースコードも本トランスパイラで他言語へ変換でき、セルフホスティングが可能

加えて、次の点も実運用上のメリットとして重視しています。

⚠ まだ開発途上にあり、実用にほど遠いかもしれません。サンプルコードなどを確認してから自己責任において、ご利用ください。

⚠ Pythonで書いたプログラム丸ごとを移植できることは期待しないでください。「Pythonで書いたコアコードが上手く変換されたらラッキーだな」ぐらいの温度感でお使いください。

## 実行速度の比較

Pythonで書かれた[サンプルコード](../../sample/readme-ja.md)の実行時間と、そのトランスパイルしたソースコードでの実行時間。（単位: 秒） 表中のPythonは元のコード、PyPyは参考用です。

|No.|内容|Python|PyPy| C++ | Rust | C# | JS | TS | Go | Java | Swift | Kotlin | Ruby | Lua | Scala3 | PHP |
|-|-|-:|-:|-:|-:|-:|-:|-:|-:|-:|-:|-:|-:|-:|-:|-:|
|01 |マンデルブロ集合（PNG）|18.647|1.091|0.790|0.781|0.383|0.768|0.806|0.753|0.756|0.760|0.756|18.955|5.500|2.221|6.159|
|02 |球の簡易レイトレーサ（PNG）|6.890|0.529|0.202|0.165|0.918|0.277|0.288|0.256|0.260|0.289|0.258|11.146|3.049|15.765|2.372|
|03 |ジュリア集合（PNG）|22.770|1.959|0.861|0.823|1.468|1.210|1.127|1.126|1.136|1.125|1.151|37.170|8.162|7.935|5.700|
|04 |オービットトラップ Julia（PNG）|11.950|1.081|0.380|0.358|0.416|0.473|0.504|0.466|0.471|0.482|0.469|28.702|4.237|7.592|3.129|
|05 |マンデルブロズーム（GIF）|14.538|1.262|0.555|0.569|1.710|0.703|0.680|0.691|0.689|0.695|0.687|14.892|17.852|8.871|5.551|
|06 |ジュリア集合パラメータ掃引（GIF）|9.627|0.507|0.546|0.407|0.329|0.626|0.619|0.622|0.621|0.624|0.629|10.704|11.122|11.067|3.694|
|07 |ライフゲーム（GIF）|5.134|0.685|0.363|0.369|1.530|1.364|1.311|1.191|1.248|1.290|1.267|11.205|8.036|5.225|0.857|
|08 |ラングトンのアリ（GIF）|5.220|0.767|0.452|0.483|2.213|2.031|1.997|1.912|2.011|1.886|2.019|18.824|10.367|6.446|2.218|
|09 |炎シミュレーション（GIF）|10.895|1.167|0.611|0.661|6.566|2.374|2.290|2.368|2.265|2.306|2.358|32.077|18.097|18.956|2.356|
|10 |プラズマエフェクト（GIF）|6.194|0.876|0.684|0.554|2.646|1.444|1.886|1.397|1.414|1.444|1.319|11.745|7.806|4.525|1.994|
|11 |リサージュ粒子（GIF）|3.582|0.532|0.356|0.359|0.714|1.425|1.406|1.389|1.365|1.371|1.413|7.950|7.809|3.406|0.131|
|12 |ソート可視化（GIF）|3.864|0.552|0.344|0.362|0.680|1.341|1.343|1.309|1.348|1.328|1.306|8.087|7.078|4.057|0.233|
|13 |迷路生成ステップ（GIF）|3.402|0.533|0.287|0.298|1.037|1.038|1.035|0.985|1.025|0.997|0.987|6.825|6.288|3.735|0.006|
|14 |簡易レイマーチング（GIF）|2.670|0.300|0.160|0.159|0.606|0.489|0.573|0.490|0.513|0.503|0.492|3.800|3.370|2.138|0.864|
|15 |波干渉ループ（GIF）|2.631|0.402|0.299|0.252|1.196|0.616|0.794|0.609|0.614|0.629|0.612|5.142|3.316|2.496|0.900|
|16 |ガラス彫刻のカオス回転（GIF）|6.847|0.606|0.277|0.246|1.220|0.650|0.822|0.638|0.643|0.667|0.643|8.743|8.059|15.675|3.987|
|17 |モンテカルロ法で円周率近似|2.981|0.105|0.019|0.018|0.098|0.431|0.433|0.432|0.433|0.436|0.436|1.988|0.534|0.279|0.638|
|18 |ミニ言語インタプリタ|2.037|0.601|0.610|0.427|0.735|0.446|0.446|0.405|0.417|0.423|0.417|7.854|2.403|0.885|1.718|

![06_julia_parameter_sweep](../../sample/images/06_julia_parameter_sweep.gif)

<details>
<summary>サンプルコード : 06_julia_parameter_sweep.py</summary>

- ソース全体: [sample/py/06_julia_parameter_sweep.py](../../sample/py/06_julia_parameter_sweep.py)

</details>

<details>
<summary>変換後コード（C++ | Rust | C# | JavaScript | TypeScript | Go | Java | Swift | Kotlin | Ruby | Lua | Scala3 | PHP）</summary>

- C++: [View full code](../../sample/cpp/06_julia_parameter_sweep.cpp)
- Rust: [View full code](../../sample/rs/06_julia_parameter_sweep.rs)
- C#: [View full code](../../sample/cs/06_julia_parameter_sweep.cs)
- JavaScript: [View full code](../../sample/js/06_julia_parameter_sweep.js)
- TypeScript: [View full code](../../sample/ts/06_julia_parameter_sweep.ts)
- Go: [View full code](../../sample/go/06_julia_parameter_sweep.go)
- Java: [View full code](../../sample/java/06_julia_parameter_sweep.java)
- Swift: [View full code](../../sample/swift/06_julia_parameter_sweep.swift)
- Kotlin: [View full code](../../sample/kotlin/06_julia_parameter_sweep.kt)
- Ruby: [View full code](../../sample/ruby/06_julia_parameter_sweep.rb)
- Lua: [View full code](../../sample/lua/06_julia_parameter_sweep.lua)
- Scala3: [View full code](../../sample/scala/06_julia_parameter_sweep.scala)
- PHP: [View full code](../../sample/php/06_julia_parameter_sweep.php)

</details>

<br/>

![16_glass_sculpture_chaos](../../sample/images/16_glass_sculpture_chaos.gif)

<details>
<summary>サンプルコード : 16_glass_sculpture_chaos.py</summary>

- ソース全体: [sample/py/16_glass_sculpture_chaos.py](../../sample/py/16_glass_sculpture_chaos.py)

</details>

<details>
<summary>変換後コード（C++ | Rust | C# | JavaScript | TypeScript | Go | Java | Swift | Kotlin | Ruby | Lua | Scala3 | PHP）</summary>

- C++: [View full code](../../sample/cpp/16_glass_sculpture_chaos.cpp)
- Rust: [View full code](../../sample/rs/16_glass_sculpture_chaos.rs)
- C#: [View full code](../../sample/cs/16_glass_sculpture_chaos.cs)
- JavaScript: [View full code](../../sample/js/16_glass_sculpture_chaos.js)
- TypeScript: [View full code](../../sample/ts/16_glass_sculpture_chaos.ts)
- Go: [View full code](../../sample/go/16_glass_sculpture_chaos.go)
- Java: [View full code](../../sample/java/16_glass_sculpture_chaos.java)
- Swift: [View full code](../../sample/swift/16_glass_sculpture_chaos.swift)
- Kotlin: [View full code](../../sample/kotlin/16_glass_sculpture_chaos.kt)
- Ruby: [View full code](../../sample/ruby/16_glass_sculpture_chaos.rb)
- Lua: [View full code](../../sample/lua/16_glass_sculpture_chaos.lua)
- Scala3: [View full code](../../sample/scala/16_glass_sculpture_chaos.scala)
- PHP: [View full code](../../sample/php/16_glass_sculpture_chaos.php)

</details>

<a id="read-the-docs-ja"></a>

## ドキュメントを読む

- 日本語チュートリアル: [tutorial/README.md](./tutorial/README.md)
- 日本語ドキュメント一覧: [index.md](./index.md)
- 英語チュートリアル: [../en/how-to-use.md](../en/how-to-use.md)
- 英語ドキュメント一覧: [../en/index.md](../en/index.md)

## ライセンス

Apache License 2.0
