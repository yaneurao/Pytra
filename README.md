<a href="docs/ja/README.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/README-日本語-DC2626?style=flat-square">
</a>

<p align="center">
  <img src="docs/images/pytra-code-alchemist-s.png" alt="Pytra Code Alchemist" width="256">
</p>

<div align="center">
    <h1>Pytra</h1>
    <img alt="Python" src="https://img.shields.io/badge/-Python-3776AB?style=flat-square&logo=python&logoColor=white"> is Pytra's input language — Pytra transpiles that code into multiple target languages.
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


## Features

**🐍 Python → native code in each target language**

- 🌐 Transpiles to C++ / Rust / Go / Java / TS and many more
- 🧩 Preserves the original code structure almost entirely
- ⚡ Write in Python, generate high-performance code
- ✨ Simple Python subset input
- 🛠 Works with existing tools like VS Code out of the box
- 🔧 The transpiler itself is written in Python — easy to extend
- 🔁 Self-hosting capable — can transpile itself

## Performance Comparison

Execution time of sample code written in Python versus execution time of the same code after transpilation. (Unit: seconds.) The Python column is the original code; PyPy is included for reference.

|No.|Description|<img alt="Python" src="https://img.shields.io/badge/-Python-3776AB?style=flat-square&logo=python&logoColor=white">|<img alt="PyPy" src="https://img.shields.io/badge/-PyPy-4B8BBE?style=flat-square">|<img alt="C++" src="https://img.shields.io/badge/-C%2B%2B-00599C?style=flat-square&logo=cplusplus&logoColor=white">|<img alt="Rust" src="https://img.shields.io/badge/-Rust-F6B73C?style=flat-square&logo=rust&logoColor=black">|<img alt="C%23" src="https://img.shields.io/badge/-C%23-239120?style=flat-square&logo=dotnet&logoColor=white">|<img alt="JS" src="https://img.shields.io/badge/-JS-F7DF1E?style=flat-square&logo=javascript&logoColor=black">|
|-|-|-:|-:|-:|-:|-:|-:|
|06 |Julia set parameter sweep (GIF)|9.627|0.507|0.546|0.407|0.329|0.626|
|16 |Glass sculpture chaos rotation (GIF)|6.847|0.606|0.277|0.246|1.220|0.650|

Full data for all languages and all samples → [Sample page](sample/README.md#performance-comparison)

<table><tr>
<td valign="top" width="50%">

![06_julia_parameter_sweep](sample/images/06_julia_parameter_sweep.gif)

<details>
<summary>Sample code : 06_julia_parameter_sweep.py</summary>

- Full source: [sample/py/06_julia_parameter_sweep.py](sample/py/06_julia_parameter_sweep.py)

</details>

<details>
<summary>Transpiled code (per language)</summary>

[C++](sample/cpp/06_julia_parameter_sweep.cpp) | [Rust](sample/rs/06_julia_parameter_sweep.rs) | [C#](sample/cs/06_julia_parameter_sweep.cs) | [JS](sample/js/06_julia_parameter_sweep.js) | [TS](sample/ts/06_julia_parameter_sweep.ts) | [Dart](sample/dart/06_julia_parameter_sweep.dart) | [Go](sample/go/06_julia_parameter_sweep.go) | [Java](sample/java/06_julia_parameter_sweep.java) | [Swift](sample/swift/06_julia_parameter_sweep.swift) | [Kotlin](sample/kotlin/06_julia_parameter_sweep.kt) | [Ruby](sample/ruby/06_julia_parameter_sweep.rb) | [Lua](sample/lua/06_julia_parameter_sweep.lua) | [Scala3](sample/scala/06_julia_parameter_sweep.scala) | [PHP](sample/php/06_julia_parameter_sweep.php) | [Julia](sample/julia/06_julia_parameter_sweep.jl)

</details>

</td>
<td valign="top" width="50%">

![16_glass_sculpture_chaos](sample/images/16_glass_sculpture_chaos.gif)

<details>
<summary>Sample code : 16_glass_sculpture_chaos.py</summary>

- Full source: [sample/py/16_glass_sculpture_chaos.py](sample/py/16_glass_sculpture_chaos.py)

</details>

<details>
<summary>Transpiled code (per language)</summary>

[C++](sample/cpp/16_glass_sculpture_chaos.cpp) | [Rust](sample/rs/16_glass_sculpture_chaos.rs) | [C#](sample/cs/16_glass_sculpture_chaos.cs) | [JS](sample/js/16_glass_sculpture_chaos.js) | [TS](sample/ts/16_glass_sculpture_chaos.ts) | [Dart](sample/dart/16_glass_sculpture_chaos.dart) | [Go](sample/go/16_glass_sculpture_chaos.go) | [Java](sample/java/16_glass_sculpture_chaos.java) | [Swift](sample/swift/16_glass_sculpture_chaos.swift) | [Kotlin](sample/kotlin/16_glass_sculpture_chaos.kt) | [Ruby](sample/ruby/16_glass_sculpture_chaos.rb) | [Lua](sample/lua/16_glass_sculpture_chaos.lua) | [Scala3](sample/scala/16_glass_sculpture_chaos.scala) | [PHP](sample/php/16_glass_sculpture_chaos.php) | [Julia](sample/julia/16_glass_sculpture_chaos.jl)

</details>

</td>
</tr></table>

## Python vs C++ vs Rust vs Pytra

Legend: ✅ = Good / 🔶 = Partial / limited / ❌ = Not supported / difficult

| Aspect | ![Python](https://img.shields.io/badge/-Python-3776AB?style=flat-square&logo=python&logoColor=white) | ![C++](https://img.shields.io/badge/-C%2B%2B-00599C?style=flat-square&logo=cplusplus&logoColor=white) | ![Rust](https://img.shields.io/badge/-Rust-F6B73C?style=flat-square&logo=rust&logoColor=black) | ![Pytra](https://img.shields.io/badge/-Pytra-875715?style=flat-square&labelColor=F4DB8E) |
|-|-|-|-|-|
| Syntax | ✅ Simple | ❌ Complex | 🔶 Ownership/<br>lifetimes | ✅ Same as Python |
| Type safety | ❌ Dynamic | ✅ Static | ✅ Static | ✅ Static<br>(Python-style annotations) |
| Execution speed | ❌ Slow | ✅ Fast | ✅ Fast | ✅ Fast<br>(depends on target) |
| Memory management | ✅ GC<br>(easy but heavy) | ❌ Manual/<br>shared_ptr | 🔶 Ownership<br>(safe but hard) | ✅ RC-based<br>automatic |
| Integer types | 🔶 Arbitrary precision only | ✅ int8–64 | ✅ i8–i64 | ✅ int8–64 |
| float | 🔶 64-bit only | ✅ 32/64-bit | ✅ f32/f64 | ✅ 32/64-bit |
| Build | ✅ Not needed | ❌ CMake etc. | 🔶 cargo | ✅ `./pytra`<br>`--build --run` |
| Multi-language output | ❌ | ❌ | ❌ | ✅ 18 languages |
| Optimization | ❌ Limited | ✅ Rich | ✅ Rich | ✅ Leverages target |
| Distribution | 🔶 Requires runtime | ✅ Binary | ✅ Binary | ✅ Language-native |
| Single inheritance | ✅ | ✅ | ❌ traits only | ✅ |
| Multiple inheritance | ✅ | 🔶 Complex | ❌ | ❌ |
| Mix-in | ✅ | 🔶 CRTP etc. | ❌ | ✅ |
| Trait/<br>Interface | 🔶 Protocol | 🔶 virtual base | ✅ Native | ✅ `@trait` |
| Exception handling | ✅ | ✅ | ❌ Result/panic | ✅ All languages |
| Templates/<br>Generics | ❌ | 🔶 Cryptic errors | ✅ | ✅ `@template` |
| Selfhost | ❌ | ❌ | ❌ | ✅ |

<a id="read-the-docs"></a>

## Read the Docs

| | ![English](https://img.shields.io/badge/English-2563EB?style=flat-square) | ![日本語](https://img.shields.io/badge/日本語-DC2626?style=flat-square) |
|---|---|---|
| Getting started | [Tutorial](docs/en/tutorial/README.md) | [チュートリアル](docs/ja/tutorial/README.md) |
| Guide | [Guides](docs/en/guide/README.md) | [ガイド](docs/ja/guide/README.md) |
| Specification | [Spec index](docs/en/spec/index.md) | [仕様書](docs/ja/spec/index.md) |
| Progress | [Project Progress](docs/en/progress/index.md) | [プロジェクト進捗](docs/ja/progress/index.md) |

## Changelog

> **2026-04-10** — P0-ZIG-CREXC-S4 complete. Zig / Rust exception / try / with handling fully shared via CommonRenderer hooks. Zig toolchain_ dependency eliminated (all languages now at 0). Nim / Go / Lua new fixture parity complete. Lua copy elision done.

> **2026-04-09** — Zig / Rust handler binding / panic / block expression helpers consolidated in CommonRenderer.

> **2026-04-08** — All languages lint clear (697→0). 18 languages at 10/10 PASS. C# / Go / Nim parity restored. Nim emitter string-split workaround eliminated. P0-ZIG-CREXC S1-S3 started.

> **2026-04-07** — Lint down to 149 / 14 languages at 10/10 PASS (697→149). PyFile abolished, IOBase hierarchy in `built_in/io.py`. Emitter guide §12.7. Cross-language PyFile coupling removal.

> **2026-04-06** — With statement via `__enter__`/`__exit__` protocol (CommonRenderer try/finally + hoist). 2 with fixtures added. TS/JS shim cleanup complete. Dart emitter guide compliance. JVM major progress. .east* removed from git.

> **2026-04-05** — containers.py `mut[T]` annotations for `meta.mutates_receiver`. C++ method name hardcode removed. mapping.json FQCN key unification. Toolchain rename complete.

[Full changelog](docs/en/changelog.md)

## License

Apache License 2.0
