<a href="../../ja/blog/index.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# Pytra Development Blog

This is where we write about Pytra's design decisions and development backstories.

---

## 2026-03-26 | Why we split the pipeline into six stages

What started as a Python -> C++ transpiler ended up supporting 17 languages before we noticed. Internally, though, it was still a huge monolith that did everything in one pass. Type resolution, syntax normalization, and emit all lived in the same file, so every new backend kept hitting the same class of bugs.

That is why we split it into six stages: parse / resolve / compile / optimize / link / emit. Each stage reads and writes JSON, and each stage can be validated independently with golden-file tests. As a result, it became immediately obvious which stage introduced a bug.

[-> Architecture guide](../tutorial/architecture.md)

---

## 2026-03-25 | Killing `signature_registry`

We used to manage facts such as "the return type of `math.sqrt` is `float64`" in a hard-coded table inside Python code. Every time the stdlib grew, we had to add entries by hand. If we forgot, the type became `unknown`, and the emitter broke.

Then we realized: if we read the function declarations in `math.py`, we already know the return types. That led us to rebuild the system so built-in and stdlib type information is derived automatically from declarations in `.py` files. Once runtime information was also declared directly on the definitions with `@extern_fn(module=..., symbol=..., tag=...)`, the hard-coded table became completely unnecessary.

---

## 2026-03-24 | Design constraints with selfhost in mind

We want to transpile Pytra's own transpiler with Pytra itself. To make that possible, the transpiler code has to be written in a subset that Pytra can already transpile.

No `Any`, no `object`, no Python standard modules (only `pytra.std.*`), no mutable global state, and no dynamic imports. The constraints are strict, but following them produces code that can be transpiled not just to C++, but also to Go and Rust.

In practice, 37 out of 46 files in `toolchain2/` already made it through parse -> resolve -> compile -> optimize. The remaining 9 files only use syntax the parser does not support yet, such as the walrus operator, so we expect all of them to pass once that support is added.
