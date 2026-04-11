<a href="../../README.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
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
    <br>
    <img alt="Java" src="https://img.shields.io/badge/-Java%C2%A0%C2%A0-ED8B00?style=flat-square&logo=openjdk&logoColor=white">
    <img alt="Scala3" src="https://img.shields.io/badge/-Scala3-10B981?style=flat-square&logo=scala&logoColor=white">
    <img alt="Kotlin" src="https://img.shields.io/badge/-Kotlin-7F52FF?style=flat-square&logo=kotlin&logoColor=white">
    <img alt="Swift" src="https://img.shields.io/badge/-Swift%C2%A0-F05138?style=flat-square&logo=swift&logoColor=white">
    <img alt="Ruby" src="https://img.shields.io/badge/-Ruby%C2%A0%C2%A0-BB1200?style=flat-square&logo=ruby&logoColor=white">
    <img alt="Lua" src="https://img.shields.io/badge/-Lua%C2%A0%C2%A0%C2%A0-4C6EF5?style=flat-square&logo=lua&logoColor=white">
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

[C++](../../sample/cpp/06_julia_parameter_sweep.cpp) | [Rust](../../sample/rs/06_julia_parameter_sweep.rs) | [C#](../../sample/cs/06_julia_parameter_sweep.cs) | [JS](../../sample/js/06_julia_parameter_sweep.js) | [TS](../../sample/ts/06_julia_parameter_sweep.ts) | [Dart](../../sample/dart/06_julia_parameter_sweep.dart) | [Go](../../sample/go/06_julia_parameter_sweep.go) | [Java](../../sample/java/06_julia_parameter_sweep.java) | [Swift](../../sample/swift/06_julia_parameter_sweep.swift) | [Kotlin](../../sample/kotlin/06_julia_parameter_sweep.kt) | [Ruby](../../sample/ruby/06_julia_parameter_sweep.rb) | [Lua](../../sample/lua/06_julia_parameter_sweep.lua) | [Scala3](../../sample/scala/06_julia_parameter_sweep.scala) | [PHP](../../sample/php/06_julia_parameter_sweep.php) | [Julia](../../sample/julia/06_julia_parameter_sweep.jl)

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

[C++](../../sample/cpp/16_glass_sculpture_chaos.cpp) | [Rust](../../sample/rs/16_glass_sculpture_chaos.rs) | [C#](../../sample/cs/16_glass_sculpture_chaos.cs) | [JS](../../sample/js/16_glass_sculpture_chaos.js) | [TS](../../sample/ts/16_glass_sculpture_chaos.ts) | [Dart](../../sample/dart/16_glass_sculpture_chaos.dart) | [Go](../../sample/go/16_glass_sculpture_chaos.go) | [Java](../../sample/java/16_glass_sculpture_chaos.java) | [Swift](../../sample/swift/16_glass_sculpture_chaos.swift) | [Kotlin](../../sample/kotlin/16_glass_sculpture_chaos.kt) | [Ruby](../../sample/ruby/16_glass_sculpture_chaos.rb) | [Lua](../../sample/lua/16_glass_sculpture_chaos.lua) | [Scala3](../../sample/scala/16_glass_sculpture_chaos.scala) | [PHP](../../sample/php/16_glass_sculpture_chaos.php) | [Julia](../../sample/julia/16_glass_sculpture_chaos.jl)

</details>

</td>
</tr></table>

## Python vs C++ vs Rust vs Pytra

凡例: ✅ = 良い / 🔶 = 部分的・制限あり / ❌ = 非対応・困難

| 観点 | ![Python](https://img.shields.io/badge/-Python-3776AB?style=flat-square&logo=python&logoColor=white) | ![C++](https://img.shields.io/badge/-C%2B%2B-00599C?style=flat-square&logo=cplusplus&logoColor=white) | ![Rust](https://img.shields.io/badge/-Rust-F6B73C?style=flat-square&logo=rust&logoColor=black) | ![Pytra](https://img.shields.io/badge/-Pytra-875715?style=flat-square&labelColor=F4DB8E) |
|-|-|-|-|-|
| 構文 | ✅ シンプル | ❌ 複雑 | 🔶 所有権/<br>ライフタイム | ✅ Pythonと同じ |
| 型安全性 | ❌ 動的 | ✅ 静的 | ✅ 静的 | ✅ 静的<br>(Python風注釈) |
| 実行速度 | ❌ 遅い | ✅ 高速 | ✅ 高速 | ✅ 高速<br>(変換先に依存) |
| メモリ管理 | ✅ GC<br>(楽だが重い) | ❌ 手動/<br>shared_ptr | 🔶 所有権<br>(安全だが難) | ✅ RCベース<br>で自動 |
| 整数型 | 🔶 多倍長のみ | ✅ int8〜64 | ✅ i8〜i64 | ✅ int8〜64 |
| float | 🔶 64-bitのみ | ✅ 32/64-bit | ✅ f32/f64 | ✅ 32/64-bit |
| ビルド | ✅ 不要 | ❌ CMake等 | 🔶 cargo | ✅ `./pytra`<br>`--build --run` |
| 多言語展開 | ❌ | ❌ | ❌ | ✅ 18言語 |
| 最適化 | ❌ 限定的 | ✅ 豊富 | ✅ 豊富 | ✅ 変換先を活用 |
| 配布 | 🔶 要runtime | ✅ バイナリ | ✅ バイナリ | ✅ 各言語固有 |
| 単一継承 | ✅ | ✅ | ❌ traitのみ | ✅ |
| 多重継承 | ✅ | 🔶 複雑 | ❌ | ❌ |
| Mix-in | ✅ | 🔶 CRTP等 | ❌ | ✅ |
| Trait/<br>Interface | 🔶 Protocol | 🔶 virtual base | ✅ ネイティブ | ✅ `@trait` |
| 例外処理 | ✅ | ✅ | ❌ Result/panic | ✅ 全言語対応 |
| テンプレート/<br>ジェネリクス | ❌ | 🔶 エラー難読 | ✅ | ✅ `@template` |
| Selfhost | ❌ | ❌ | ❌ | ✅ |

<a id="read-the-docs-ja"></a>

## ドキュメントを読む

| | ![English](https://img.shields.io/badge/English-2563EB?style=flat-square) | ![日本語](https://img.shields.io/badge/日本語-DC2626?style=flat-square) |
|---|---|---|
| Getting started | [Tutorial](../en/tutorial/README.md) | [チュートリアル](./tutorial/README.md) |
| Guide | [Guides](../en/guide/README.md) | [ガイド](./guide/README.md) |
| Specification | [Spec index](../en/spec/index.md) | [仕様書](./spec/index.md) |
| Progress | [Project Progress](../en/progress/index.md) | [プロジェクト進捗](./progress/index.md) |

## 更新履歴

> **2026-04-10** — P0-ZIG-CREXC-S4 完了。Zig / Rust の exception / try / with 処理を CommonRenderer hook 経由で完全共有。Zig toolchain_ 依存解消（全言語 toolchain_ 依存 0）。Nim / Go / Lua 新規 fixture parity 完了。Lua copy elision 完成。

> **2026-04-09** — Zig / Rust の handler binding / panic / block expression helper を CommonRenderer に集約。

> **2026-04-08** — 全言語 lint 完全クリア達成（697→0）。18 言語全て 10/10 PASS。C# / Go / Nim parity 復旧。Nim emitter の文字列分割偽装撲滅。P0-ZIG-CREXC S1-S3 開始（Zig / Rust 例外処理の CommonRenderer 集約）。

> **2026-04-07** — lint 149 件 / 14 言語 10/10 PASS（697→149）。PyFile 廃止、IOBase 型階層を `built_in/io.py` に定義。emitter guide §12.7 追加。全言語横断で PyFile coupling 除去。

> **2026-04-06** — with 文を `__enter__`/`__exit__` プロトコルで実装（CommonRenderer try/finally + hoist）。with fixture 2 件追加。TS/JS shim cleanup 完了。Dart emitter guide 準拠。JVM backend 大幅進展。.east* 生成物を git 管理から除去。

> **2026-04-05** — containers.py `mut[T]` 注釈で `meta.mutates_receiver` 導入。C++ メソッド名ハードコード解消。mapping.json FQCN キー統一完了。toolchain リネーム完了。

[全履歴はこちら](./changelog.md)

## ライセンス

Apache License 2.0
