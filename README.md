<a href="docs/ja/README.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/README-日本語-2563EB?style=flat-square">
</a>

<p align="center">
  <img src="docs/images/pytra-code-alchemist-s.png" alt="Pytra Code Alchemist" width="256">
</p>

<div align="center">
    <h1>Pytra</h1>
    <img alt="Python" src="https://img.shields.io/badge/-Python-3776AB?style=flat-square&logo=python&logoColor=white"> is Pytra's source language. Pytra transpiles that code into multiple target languages.
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


## Features of Pytra

**🐍 Python → Native code in each target language**

- 🌐 Transpiles to C++, Rust, Go, Java, TS, and many more
- 🧩 Preserves the original program structure almost as-is
- ⚡ Generates high-performance code even when you write in Python
- ✨ Uses a simple Python subset
- 🛠 Works with existing tools such as VS Code
- 🔧 The core is also written in Python, so it is easy to extend
- 🔁 Supports self-hosting

## Runtime Performance Comparison

These are execution times for sample programs written in Python and for their transpiled source code. Unit: seconds. In the table, Python is the original implementation and PyPy is included as a reference.

|No.|Workload|<img alt="Python" src="https://img.shields.io/badge/-Python-3776AB?style=flat-square&logo=python&logoColor=white">|<img alt="PyPy" src="https://img.shields.io/badge/-PyPy-4B8BBE?style=flat-square">|<img alt="C++" src="https://img.shields.io/badge/-C%2B%2B-00599C?style=flat-square&logo=cplusplus&logoColor=white">|<img alt="Rust" src="https://img.shields.io/badge/-Rust-F6B73C?style=flat-square&logo=rust&logoColor=black">|<img alt="C#" src="https://img.shields.io/badge/-C%23-239120?style=flat-square&logo=dotnet&logoColor=white">|<img alt="JS" src="https://img.shields.io/badge/-JS-F7DF1E?style=flat-square&logo=javascript&logoColor=black">|
|-|-|-:|-:|-:|-:|-:|-:|
|06 |Julia-set parameter sweep (GIF)|9.627|0.507|0.546|0.407|0.329|0.626|
|16 |Chaotic rotation of a glass sculpture (GIF)|6.847|0.606|0.277|0.246|1.220|0.650|

Full data for all languages and all samples: [Sample page](sample/README.md#runtime-performance-comparison)

<table><tr>
<td valign="top" width="50%">

![06_julia_parameter_sweep](sample/images/06_julia_parameter_sweep.gif)

<details>
<summary>Sample code: 06_julia_parameter_sweep.py</summary>

- Full source: [sample/py/06_julia_parameter_sweep.py](sample/py/06_julia_parameter_sweep.py)

</details>

<details>
<summary>Transpiled code in each language</summary>

[C++](sample/cpp/06_julia_parameter_sweep.cpp) | [Rust](sample/rs/06_julia_parameter_sweep.rs) | [C#](sample/cs/06_julia_parameter_sweep.cs) | [JS](sample/js/06_julia_parameter_sweep.js) | [TS](sample/ts/06_julia_parameter_sweep.ts) | [Dart](sample/dart/06_julia_parameter_sweep.dart) | [Go](sample/go/06_julia_parameter_sweep.go) | [Java](sample/java/06_julia_parameter_sweep.java) | [Swift](sample/swift/06_julia_parameter_sweep.swift) | [Kotlin](sample/kotlin/06_julia_parameter_sweep.kt) | [Ruby](sample/ruby/06_julia_parameter_sweep.rb) | [Lua](sample/lua/06_julia_parameter_sweep.lua) | [Scala3](sample/scala/06_julia_parameter_sweep.scala) | [PHP](sample/php/06_julia_parameter_sweep.php) | [Julia](sample/julia/06_julia_parameter_sweep.jl)

</details>

</td>
<td valign="top" width="50%">

![16_glass_sculpture_chaos](sample/images/16_glass_sculpture_chaos.gif)

<details>
<summary>Sample code: 16_glass_sculpture_chaos.py</summary>

- Full source: [sample/py/16_glass_sculpture_chaos.py](sample/py/16_glass_sculpture_chaos.py)

</details>

<details>
<summary>Transpiled code in each language</summary>

[C++](sample/cpp/16_glass_sculpture_chaos.cpp) | [Rust](sample/rs/16_glass_sculpture_chaos.rs) | [C#](sample/cs/16_glass_sculpture_chaos.cs) | [JS](sample/js/16_glass_sculpture_chaos.js) | [TS](sample/ts/16_glass_sculpture_chaos.ts) | [Dart](sample/dart/16_glass_sculpture_chaos.dart) | [Go](sample/go/16_glass_sculpture_chaos.go) | [Java](sample/java/16_glass_sculpture_chaos.java) | [Swift](sample/swift/16_glass_sculpture_chaos.swift) | [Kotlin](sample/kotlin/16_glass_sculpture_chaos.kt) | [Ruby](sample/ruby/16_glass_sculpture_chaos.rb) | [Lua](sample/lua/16_glass_sculpture_chaos.lua) | [Scala3](sample/scala/16_glass_sculpture_chaos.scala) | [PHP](sample/php/16_glass_sculpture_chaos.php) | [Julia](sample/julia/16_glass_sculpture_chaos.jl)

</details>

</td>
</tr></table>

## Python vs Pytra

|Aspect|Python|Pytra|
|-|-|-|
|Execution|Runs on the Python interpreter|Runs in each backend language|
|Integers|Arbitrary precision|`int64`, `uint64`, ..., `int8`, `uint8`|
|Floating point|64-bit|64-bit / 32-bit|
|Runtime speed|x1|x10 to x100 when transpiled to C++ or Rust|
|Backend optimization|Limited|Extensive|
|Multi-language deployment|❌|✅|
|Typing|Dynamic typing|Static typing|
|Bounds checks|Always enabled|Customizable|
|Platform integration|Python-centric|Fits each language's SDKs and tools|
|Distribution|Requires Python runtime|Uses each language's native distribution model|
|Multiple inheritance|✅|❌, single inheritance only|
|Mix-ins|✅|✅|
|Self-hosting|❌|✅|

⚠ This project is still under active development and may be far from practical use. Review the sample code and use it at your own risk.

<a id="read-the-docs"></a>

## Read the Docs

- Japanese tutorial: [docs/ja/tutorial/README.md](docs/ja/tutorial/README.md)
- Architecture: [docs/ja/tutorial/architecture.md](docs/ja/tutorial/architecture.md) - an overview of the pipeline
- Japanese document index: [docs/ja/index.md](docs/ja/index.md)
- English tutorial: [docs/en/tutorial/how-to-use.md](docs/en/tutorial/how-to-use.md)
- English document index: [docs/en/index.md](docs/en/index.md)

## Changelog

> **2026-03-26** - Pipeline redesign completed. All six stages of the pipeline (`parse -> resolve -> compile -> optimize -> link -> emit`) now work end to end. The Go backend has been migrated to the new pipeline.

> **2026-03-25** - All P0 tasks completed. Reorganized the `test/` directory. Go emitter and runtime reached parity on all 18 samples.

> **2026-03-24** - Started the pipeline redesign. Added `toolchain2/`, implemented `pytra-cli2`, and defined the EAST1/EAST2 specifications.

Full history: [docs/ja/changelog.md](docs/ja/changelog.md)

## License

Apache License 2.0
