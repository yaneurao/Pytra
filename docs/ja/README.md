
<a href="../../README.md">
  <img alt="Read in English" src="https://img.shields.io/badge/README-English-2563EB?style=flat-square">
</a>

<p align="center">
  <img src="../images/pytra-code-alchemist-s.png" alt="Pytra Code Alchemist" width="256">
</p>

<div align="center">
    <h1>Pytra</h1>
    <img alt="Python" src="https://img.shields.io/badge/-Python-3776AB?style=flat-square&logo=python&logoColor=white"> は Pytra の入力言語で、Pytra はそのコードを複数のターゲット言語へトランスパイルします。
</div>

<div align="center">
    <br><code>·  Supported Backends  ·</code><br><br>
    <img alt="C++" src="https://img.shields.io/badge/-C%2B%2B%C2%A0%C2%A0%C2%A0-00599C?style=flat-square&logo=cplusplus&logoColor=white">
    <img alt="Rust" src="https://img.shields.io/badge/-Rust%C2%A0%C2%A0-F6B73C?style=flat-square&logo=rust&logoColor=black">
    <img alt="C#" src="https://img.shields.io/badge/-C%23%C2%A0%C2%A0%C2%A0%C2%A0-239120?style=flat-square&logo=dotnet&logoColor=white">
    <img alt="PowerShell" src="https://img.shields.io/badge/-PowerShell-5391FE?style=flat-square&logo=powershell&logoColor=white">
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
    <img alt="Zig" src="https://img.shields.io/badge/-Zig-F7C948?style=flat-square&logo=zig&logoColor=black">
    <br>
</div>


## Pytraの特徴

**🐍 Python → 各言語のネイティブコードへ**

- 🌐 C++ / Rust / Go / Java / TS ほか多数へ変換
- 🧩 元コードの構造をほぼそのまま維持
- ⚡ Pythonで書いても高性能コードを生成
- ✨ Pythonサブセットでシンプル
- 🛠 VS Codeなど既存ツールがそのまま使える
- 🔧 本体もPython製で拡張しやすい
- 🔁 自己変換できるセルフホスティング対応

## 実行速度の比較

Pythonで書かれたサンプルコードの実行時間と、そのトランスパイルしたソースコードでの実行時間。（単位: 秒） 表中のPythonは元のコード、PyPyは参考用です。

|No.|内容|<img alt="Python" src="https://img.shields.io/badge/-Python-3776AB?style=flat-square&logo=python&logoColor=white">|<img alt="PyPy" src="https://img.shields.io/badge/-PyPy-4B8BBE?style=flat-square">|<img alt="C++" src="https://img.shields.io/badge/-C%2B%2B-00599C?style=flat-square&logo=cplusplus&logoColor=white">|<img alt="Rust" src="https://img.shields.io/badge/-Rust-F6B73C?style=flat-square&logo=rust&logoColor=black">|<img alt="C%23" src="https://img.shields.io/badge/-C%23-239120?style=flat-square&logo=dotnet&logoColor=white">|<img alt="JS" src="https://img.shields.io/badge/-JS-F7DF1E?style=flat-square&logo=javascript&logoColor=black">|
|-|-|-:|-:|-:|-:|-:|-:|
|06 |ジュリア集合パラメータ掃引（GIF）|9.627|0.507|0.546|0.407|0.329|0.626|
|16 |ガラス彫刻のカオス回転（GIF）|6.847|0.606|0.277|0.246|1.220|0.650|

全言語・全サンプルのデータ → [サンプルページ](../../sample/README-ja.md#実行速度の比較)

<table><tr>
<td valign="top" width="50%">

![06_julia_parameter_sweep](../../sample/images/06_julia_parameter_sweep.gif)

<details>
<summary>サンプルコード : 06_julia_parameter_sweep.py</summary>

- ソース全体: [sample/py/06_julia_parameter_sweep.py](../../sample/py/06_julia_parameter_sweep.py)

</details>

<details>
<summary>変換後コード（各言語）</summary>

[C++](../../sample/cpp/06_julia_parameter_sweep.cpp) | [Rust](../../sample/rs/06_julia_parameter_sweep.rs) | [C#](../../sample/cs/06_julia_parameter_sweep.cs) | [JS](../../sample/js/06_julia_parameter_sweep.js) | [TS](../../sample/ts/06_julia_parameter_sweep.ts) | [Go](../../sample/go/06_julia_parameter_sweep.go) | [Java](../../sample/java/06_julia_parameter_sweep.java) | [Swift](../../sample/swift/06_julia_parameter_sweep.swift) | [Kotlin](../../sample/kotlin/06_julia_parameter_sweep.kt) | [Ruby](../../sample/ruby/06_julia_parameter_sweep.rb) | [Lua](../../sample/lua/06_julia_parameter_sweep.lua) | [Scala3](../../sample/scala/06_julia_parameter_sweep.scala) | [PHP](../../sample/php/06_julia_parameter_sweep.php)

</details>

</td>
<td valign="top" width="50%">

![16_glass_sculpture_chaos](../../sample/images/16_glass_sculpture_chaos.gif)

<details>
<summary>サンプルコード : 16_glass_sculpture_chaos.py</summary>

- ソース全体: [sample/py/16_glass_sculpture_chaos.py](../../sample/py/16_glass_sculpture_chaos.py)

</details>

<details>
<summary>変換後コード（各言語）</summary>

[C++](../../sample/cpp/16_glass_sculpture_chaos.cpp) | [Rust](../../sample/rs/16_glass_sculpture_chaos.rs) | [C#](../../sample/cs/16_glass_sculpture_chaos.cs) | [JS](../../sample/js/16_glass_sculpture_chaos.js) | [TS](../../sample/ts/16_glass_sculpture_chaos.ts) | [Go](../../sample/go/16_glass_sculpture_chaos.go) | [Java](../../sample/java/16_glass_sculpture_chaos.java) | [Swift](../../sample/swift/16_glass_sculpture_chaos.swift) | [Kotlin](../../sample/kotlin/16_glass_sculpture_chaos.kt) | [Ruby](../../sample/ruby/16_glass_sculpture_chaos.rb) | [Lua](../../sample/lua/16_glass_sculpture_chaos.lua) | [Scala3](../../sample/scala/16_glass_sculpture_chaos.scala) | [PHP](../../sample/php/16_glass_sculpture_chaos.php)

</details>

</td>
</tr></table>

## Python vs Pytra

|観点|Python|Pytra|
|-|-|-|
|実行|Pythonインタプリタで実行|backendの各言語で実行|
|整数|多倍長|int64,uint64,..,int8,uint8|
|float|64-bit|64/32-bit|
|実行速度|x1|x10～x100(C++/Rustに変換時)|
|Backend最適化|限定的|豊富|
|多言語展開|❌|✅|
|型|動的型付け|静的型付け|
|境界チェック|常に|カスタマイズ可能|
|Platform統合|Python中心|各言語のSDKs/toolsと馴染む|
|配布|Python runtimeが必要|各言語固有の配布|
|多重継承|✅|❌（単一継承）|
|mix-in|✅|✅|
|Selfhost|❌|✅|

⚠ まだ開発途上にあり、実用にほど遠いかもしれません。サンプルコードなどを確認してから自己責任において、ご利用ください。

<a id="read-the-docs-ja"></a>

## ドキュメントを読む

- 日本語チュートリアル: [tutorial/README.md](./tutorial/README.md)
- 日本語ドキュメント一覧: [index.md](./index.md)
- 英語チュートリアル: [../en/how-to-use.md](../en/how-to-use.md)
- 英語ドキュメント一覧: [../en/index.md](../en/index.md)

<details>
<summary>最新ニュース</summary>

> **2026-03-20 | v0.15.0 リリース**<br>
> バージョン 0.15.0 リリース。backendとしてPowerShellをサポートしました。

> **2026-03-18 | v0.14.0 リリース**<br>
> バージョン 0.14.0 リリース。[再帰的union type](spec/spec-tagged-union.md)をサポートしました。

> **2026-03-11 | v0.13.0 リリース**<br>
> バージョン 0.13.0 リリース。NES(ファミコン)のエミュレーターをPython + SDL3で書きました。[スーパーマリオ3が動きました。](https://x.com/yaneuraou/status/2031612549658202538) 非常に遅いです。これをPytraでC++に変換できるように、現在Pytra側を改良中です。

- 過去ニュース: [docs/ja/news/index.md](news/index.md)

</details>

## ライセンス

Apache License 2.0
