<a href="docs/ja/README.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/README-日本語-2563EB?style=flat-square">
</a>

<p align="center">
  <img src="docs/images/pytra-code-alchemist-s.png" alt="Pytra Code Alchemist" width="256">
</p>

<div align="center">
    <h1>Pytra</h1>
    <img alt="Python" src="https://img.shields.io/badge/-Python-3776AB?style=flat-square&logo=python&logoColor=white"> (subset) is the source language for Pytra, which transpiles code into multiple target languages.
    <p><a href="#read-the-docs">Read the Docs</a></p>
</div>

<div align="center">
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
    PowerShell, Dart, Julia, and Zig are currently in progress.
</div>

## Latest News

> **2026-03-18 | v0.14.0 Released**<br>
> Version 0.14.0 was released. Added support for [recursive union types](docs/ja/spec/spec-tagged-union.md).

> **2026-03-11 | v0.13.0 Released**<br>
> Version 0.13.0 was released. I wrote an NES (Famicom) emulator in Python + SDL3. [Super Mario Bros. 3 is running.](https://x.com/yaneuraou/status/2031612549658202538) It is very slow. I am currently improving Pytra so this can be transpiled to C++ with Pytra.

> **2026-03-10 | v0.12.0 Released**<br>
> Version 0.12.0 was released. I am currently in the middle of a large runtime reorganization.

> **2026-03-09 | v0.11.0 Released**<br>
> Version 0.11.0 was released. We are revisiting object boundaries, and the tutorial has been improved.

> **2026-03-08 | v0.10.0 Released**<br>
> Version 0.10.0 was released. `@template` is now available, and runtime support for each target language is currently being refined.

- Past News: [docs/en/news/index.md](docs/en/news/index.md)
- Current backend parity status: [docs/en/language/backend-parity-matrix.md](docs/en/language/backend-parity-matrix.md)
- Current backend test green status: [docs/en/language/backend-test-matrix.md](docs/en/language/backend-test-matrix.md)

## Features

Pytra's features

- Python to multi-language transpiler
  - Supports conversion to C++, C#, Rust, JavaScript, TypeScript, Go, Java, Swift, Kotlin, Ruby, Lua, Scala3, and PHP.
  - Converts code to output in a form extremely close to the original source.
  - The goal is to write Python code that produces output equivalent to writing directly in C++.

- Simple language model
  - Basically a subset of Python.
  - Can be developed with existing tools such as VS Code.

- High extensibility
  - The transpiler core is implemented in Python, making extension and customization easy.
  - The transpiler's own source code can be transpiled into other languages by this transpiler, enabling self-hosting.

## Python vs Pytra

|Aspect|Python|Pytra|
|-|-|-|
|Execution|Runs on Python interpreter|Runs on each target language|
|Integers|Arbitrary precision|int64, uint64, ..., int8, uint8|
|Float|64-bit|64/32-bit|
|Speed|x1|x10~x100 (when converting to C++/Rust)|
|Backend optimization|Limited|Abundant|
|Multi-language delivery|❌|✅|
|Typing|Dynamic typing|Static typing|
|Boundary checks|Always|Customizable|
|Platform integration|Python-centric|Fits each language's SDKs/tools|
|Distribution|Python runtime required|Fits language-specific deployment|
|mix-in|✅|✅|
|Multiple inheritance|✅|❌ (single inheritance)|
|Selfhost|❌|✅|

⚠ This project is still under active development and may be far from production-ready. Review sample code first and use at your own risk.

## Runtime Performance Comparison

Execution times for sample programs written in Python and their transpiled versions (unit: seconds). In the table, Python is the original code and PyPy is for reference.

|No.|Workload|<img alt="Python" src="https://img.shields.io/badge/-Python-3776AB?style=flat-square&logo=python&logoColor=white">|<img alt="PyPy" src="https://img.shields.io/badge/-PyPy-4B8BBE?style=flat-square">|<img alt="C++" src="https://img.shields.io/badge/-C%2B%2B-00599C?style=flat-square&logo=cplusplus&logoColor=white">|<img alt="Rust" src="https://img.shields.io/badge/-Rust-F6B73C?style=flat-square&logo=rust&logoColor=black">|<img alt="C#" src="https://img.shields.io/badge/-C%23-239120?style=flat-square&logo=dotnet&logoColor=white">|<img alt="JS" src="https://img.shields.io/badge/-JS-F7DF1E?style=flat-square&logo=javascript&logoColor=black">|
|-|-|-:|-:|-:|-:|-:|-:|
|06 |Julia parameter sweep (GIF)|9.627|0.507|0.546|0.407|0.329|0.626|
|16 |Chaos rotation of glass sculpture (GIF)|6.847|0.606|0.277|0.246|1.220|0.650|

Full data for all languages and samples → [Sample page](sample/readme.md#runtime-performance-comparison)

<table><tr>
<td valign="top" width="50%">

![06_julia_parameter_sweep](sample/images/06_julia_parameter_sweep.gif)

<details>
<summary>Sample code: 06_julia_parameter_sweep.py</summary>

- View full source: [sample/py/06_julia_parameter_sweep.py](sample/py/06_julia_parameter_sweep.py)

</details>

<details>
<summary>Transpiled code (all languages)</summary>

[C++](sample/cpp/06_julia_parameter_sweep.cpp) | [Rust](sample/rs/06_julia_parameter_sweep.rs) | [C#](sample/cs/06_julia_parameter_sweep.cs) | [JS](sample/js/06_julia_parameter_sweep.js) | [TS](sample/ts/06_julia_parameter_sweep.ts) | [Go](sample/go/06_julia_parameter_sweep.go) | [Java](sample/java/06_julia_parameter_sweep.java) | [Swift](sample/swift/06_julia_parameter_sweep.swift) | [Kotlin](sample/kotlin/06_julia_parameter_sweep.kt) | [Ruby](sample/ruby/06_julia_parameter_sweep.rb) | [Scala3](sample/scala/06_julia_parameter_sweep.scala) | [PHP](sample/php/06_julia_parameter_sweep.php)

</details>

</td>
<td valign="top" width="50%">

![16_glass_sculpture_chaos](sample/images/16_glass_sculpture_chaos.gif)

<details>
<summary>Sample code: 16_glass_sculpture_chaos.py</summary>

- View full source: [sample/py/16_glass_sculpture_chaos.py](sample/py/16_glass_sculpture_chaos.py)

</details>

<details>
<summary>Transpiled code (all languages)</summary>

[C++](sample/cpp/16_glass_sculpture_chaos.cpp) | [Rust](sample/rs/16_glass_sculpture_chaos.rs) | [C#](sample/cs/16_glass_sculpture_chaos.cs) | [JS](sample/js/16_glass_sculpture_chaos.js) | [TS](sample/ts/16_glass_sculpture_chaos.ts) | [Go](sample/go/16_glass_sculpture_chaos.go) | [Java](sample/java/16_glass_sculpture_chaos.java) | [Swift](sample/swift/16_glass_sculpture_chaos.swift) | [Kotlin](sample/kotlin/16_glass_sculpture_chaos.kt) | [Ruby](sample/ruby/16_glass_sculpture_chaos.rb) | [Scala3](sample/scala/16_glass_sculpture_chaos.scala) | [PHP](sample/php/16_glass_sculpture_chaos.php)

</details>

</td>
</tr></table>

## Read the Docs

- English tutorial: [docs/en/tutorial/README.md](docs/en/tutorial/README.md)
- English docs top: [docs/en/index.md](docs/en/index.md)
- Japanese tutorial: [docs/ja/tutorial/README.md](docs/ja/tutorial/README.md)
- Japanese docs top: [docs/ja/README.md](docs/ja/README.md)

## License

Apache License 2.0
