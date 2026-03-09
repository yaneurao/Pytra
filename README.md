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

## Latest News

> **2026-03-08 | v0.10.0 Released**<br>
> Version 0.10.0 was released. `@template` is now available, and runtime support for each target language is currently being refined.

> **2026-03-07 | v0.9.0 Released**<br>
> Version 0.9.0 was released. The large-scale refactor is complete, and all target languages are usable again.<br>
> `@extern` and `@abi` are now available, so transpiled code can now be called from other languages as well.

> **2026-03-06 | v0.8.0 Released**<br>
> Version 0.8.0 was released. The ABI boundary is being redefined, and a large-scale refactor is in progress. At the moment, backends other than the C++ transpiler are broken, so please use v0.7.0.

- Past News: [docs/en/news/index.md](docs/en/news/index.md)

## Features

Pytra's features

- Python to multi-language transpiler
  - Supports conversion to C++, C#, Rust, JavaScript, TypeScript, Go, Java, Swift, Kotlin, Ruby, Lua, Scala3, and PHP.
  - Converts code to output in a form extremely close to the original source.

- Write Python code that targets C++-level output quality
  - `int` defaults to 64-bit signed integer.
  - No dynamic typing.

- Simple language model
  - Basically a subset of Python.
  - Can be developed with existing tools such as VS Code.
  - Drops multiple inheritance and keeps only single inheritance.

- High extensibility
  - The transpiler core is implemented in Python, making extension and customization easy.
  - The transpiler's own source code can be transpiled into other languages by this transpiler, enabling self-hosting.

We also prioritize practical operational benefits.

WARNING: This project is still under active development and may be far from production-ready. Review sample code first and use at your own risk.

WARNING: Do not expect entire Python applications to be portable as-is. A realistic expectation is: if the core logic you wrote in Python transpiles well, that is a good outcome.

## Runtime Performance Comparison

Execution times for [sample programs](sample/readme.md) written in Python and their transpiled versions (unit: seconds). In the table, Python is the original code and PyPy is for reference.

|No.|Workload|Python|PyPy| C++ | Rust | C# | JS | TS | Go | Java | Swift | Kotlin | Ruby | Lua | Scala3 | PHP |
|-|-|-:|-:|-:|-:|-:|-:|-:|-:|-:|-:|-:|-:|-:|-:|-:|
|01 |Mandelbrot set (PNG)|18.647|1.091|0.790|0.781|0.383|0.768|0.806|0.753|0.756|0.760|0.756|18.955|5.500|2.221|6.159|
|02 |Simple sphere ray tracer (PNG)|6.890|0.529|0.202|0.165|0.918|0.277|0.288|0.256|0.260|0.289|0.258|11.146|3.049|15.765|2.372|
|03 |Julia set (PNG)|22.770|1.959|0.861|0.823|1.468|1.210|1.127|1.126|1.136|1.125|1.151|37.170|8.162|7.935|5.700|
|04 |Orbit-trap Julia set (PNG)|11.950|1.081|0.380|0.358|0.416|0.473|0.504|0.466|0.471|0.482|0.469|28.702|4.237|7.592|3.129|
|05 |Mandelbrot zoom (GIF)|14.538|1.262|0.555|0.569|1.710|0.703|0.680|0.691|0.689|0.695|0.687|14.892|17.852|8.871|5.551|
|06 |Julia parameter sweep (GIF)|9.627|0.507|0.546|0.407|0.329|0.626|0.619|0.622|0.621|0.624|0.629|10.704|11.122|11.067|3.694|
|07 |Game of Life (GIF)|5.134|0.685|0.363|0.369|1.530|1.364|1.311|1.191|1.248|1.290|1.267|11.205|8.036|5.225|0.857|
|08 |Langton's Ant (GIF)|5.220|0.767|0.452|0.483|2.213|2.031|1.997|1.912|2.011|1.886|2.019|18.824|10.367|6.446|2.218|
|09 |Flame simulation (GIF)|10.895|1.167|0.611|0.661|6.566|2.374|2.290|2.368|2.265|2.306|2.358|32.077|18.097|18.956|2.356|
|10 |Plasma effect (GIF)|6.194|0.876|0.684|0.554|2.646|1.444|1.886|1.397|1.414|1.444|1.319|11.745|7.806|4.525|1.994|
|11 |Lissajous particles (GIF)|3.582|0.532|0.356|0.359|0.714|1.425|1.406|1.389|1.365|1.371|1.413|7.950|7.809|3.406|0.131|
|12 |Sorting visualization (GIF)|3.864|0.552|0.344|0.362|0.680|1.341|1.343|1.309|1.348|1.328|1.306|8.087|7.078|4.057|0.233|
|13 |Maze generation steps (GIF)|3.402|0.533|0.287|0.298|1.037|1.038|1.035|0.985|1.025|0.997|0.987|6.825|6.288|3.735|0.006|
|14 |Simple ray marching (GIF)|2.670|0.300|0.160|0.159|0.606|0.489|0.573|0.490|0.513|0.503|0.492|3.800|3.370|2.138|0.864|
|15 |Wave interference loop (GIF)|2.631|0.402|0.299|0.252|1.196|0.616|0.794|0.609|0.614|0.629|0.612|5.142|3.316|2.496|0.900|
|16 |Chaos rotation of glass sculpture (GIF)|6.847|0.606|0.277|0.246|1.220|0.650|0.822|0.638|0.643|0.667|0.643|8.743|8.059|15.675|3.987|
|17 |Monte Carlo Pi approximation|2.981|0.105|0.019|0.018|0.098|0.431|0.433|0.432|0.433|0.436|0.436|1.988|0.534|0.279|0.638|
|18 |Mini-language interpreter|2.037|0.601|0.610|0.427|0.735|0.446|0.446|0.405|0.417|0.423|0.417|7.854|2.403|0.885|1.718|

![06_julia_parameter_sweep](sample/images/06_julia_parameter_sweep.gif)

<details>
<summary>Sample code: 06_julia_parameter_sweep.py</summary>

- View full source: [sample/py/06_julia_parameter_sweep.py](sample/py/06_julia_parameter_sweep.py)

</details>

<details>
<summary>Transpiled code (C++ | Rust | C# | JavaScript | TypeScript | Go | Java | Swift | Kotlin | Ruby | Scala3 | PHP)</summary>

- C++: [View full code](sample/cpp/06_julia_parameter_sweep.cpp)
- Rust: [View full code](sample/rs/06_julia_parameter_sweep.rs)
- C#: [View full code](sample/cs/06_julia_parameter_sweep.cs)
- JavaScript: [View full code](sample/js/06_julia_parameter_sweep.js)
- TypeScript: [View full code](sample/ts/06_julia_parameter_sweep.ts)
- Go: [View full code](sample/go/06_julia_parameter_sweep.go)
- Java: [View full code](sample/java/06_julia_parameter_sweep.java)
- Swift: [View full code](sample/swift/06_julia_parameter_sweep.swift)
- Kotlin: [View full code](sample/kotlin/06_julia_parameter_sweep.kt)
- Ruby: [View full code](sample/ruby/06_julia_parameter_sweep.rb)
- Scala3: [View full code](sample/scala/06_julia_parameter_sweep.scala)
- PHP: [View full code](sample/php/06_julia_parameter_sweep.php)

</details>

<br/>

![16_glass_sculpture_chaos](sample/images/16_glass_sculpture_chaos.gif)

<details>
<summary>Sample code: 16_glass_sculpture_chaos.py</summary>

- View full source: [sample/py/16_glass_sculpture_chaos.py](sample/py/16_glass_sculpture_chaos.py)

</details>

<details>
<summary>Transpiled code (C++ | Rust | C# | JavaScript | TypeScript | Go | Java | Swift | Kotlin | Ruby | Scala3 | PHP)</summary>

- C++: [View full code](sample/cpp/16_glass_sculpture_chaos.cpp)
- Rust: [View full code](sample/rs/16_glass_sculpture_chaos.rs)
- C#: [View full code](sample/cs/16_glass_sculpture_chaos.cs)
- JavaScript: [View full code](sample/js/16_glass_sculpture_chaos.js)
- TypeScript: [View full code](sample/ts/16_glass_sculpture_chaos.ts)
- Go: [View full code](sample/go/16_glass_sculpture_chaos.go)
- Java: [View full code](sample/java/16_glass_sculpture_chaos.java)
- Swift: [View full code](sample/swift/16_glass_sculpture_chaos.swift)
- Kotlin: [View full code](sample/kotlin/16_glass_sculpture_chaos.kt)
- Ruby: [View full code](sample/ruby/16_glass_sculpture_chaos.rb)
- Scala3: [View full code](sample/scala/16_glass_sculpture_chaos.scala)
- PHP: [View full code](sample/php/16_glass_sculpture_chaos.php)

</details>

## Read the Docs

- English docs: [docs/en/index.md](docs/en/index.md)
- Getting Started (English): [docs/en/how-to-use.md](docs/en/how-to-use.md)
- Japanese tutorial: [docs/ja/tutorial/README.md](docs/ja/tutorial/README.md)
- Japanese docs top: [docs/ja/README.md](docs/ja/README.md)

## License

Apache License 2.0
