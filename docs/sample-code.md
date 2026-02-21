# About Sample Code

<a href="../docs-jp/sample-code.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>


## 1. Purpose

`sample/` is a directory for transpiling practical Python samples into each target language and comparing execution results and runtime.

## 2. Directory Structure

- [sample/py](../sample/py): Source Python samples (currently `01` to `16`)
- [sample/cpp](../sample/cpp): C++ transpilation outputs
- [sample/cs](../sample/cs): C# transpilation outputs
- [sample/rs](../sample/rs): Rust transpilation outputs
- [sample/js](../sample/js): JavaScript transpilation outputs
- [sample/ts](../sample/ts): TypeScript transpilation outputs
- [sample/go](../sample/go): Go transpilation outputs
- [sample/java](../sample/java): Java transpilation outputs
- [sample/swift](../sample/swift): Swift transpilation outputs
- [sample/kotlin](../sample/kotlin): Kotlin transpilation outputs
- `sample/obj`: Build artifacts for each language (not tracked by Git)
- `sample/out`: Runtime output images (PNG/GIF, not tracked by Git)

## 3. Measurement Conditions (README Table Baseline)

- Python: `PYTHONPATH=src python3 sample/py/<file>.py`
- C++: `g++ -std=c++20 -O3 -ffast-math -flto -I src ...`
- C#: `mcs ...` + `mono ...`
- Rust: `rustc -O ...`
- JavaScript: `node sample/js/<file>.js`
- TypeScript: Compile with `tsc ...`, then run with `node ...`
- Go: `go run` or execute after `go build`
- Java: `javac` + `java`
- Swift: Executable built with `swiftc`
- Kotlin: `jar` built with `kotlinc -include-runtime`

Note:
- `py2swift.py` / `py2kotlin.py` currently use the Node backend approach and execute with `node` at runtime (they do not invoke `python3`).

## 4. Runtime Notes

- When running `sample/py/` as Python directly, add `PYTHONPATH=src` for `pylib` resolution.

```bash
PYTHONPATH=src python3 sample/py/01_mandelbrot.py
```

## 5. Relation To Test Code

`test/` and `sample/` have different roles: `test/` is for small feature checks, `sample/` is for practical, heavier-load cases.

- [test/fixtures](../test/fixtures): Source test code for transpilation
- [test/unit](../test/unit): Unit tests
- `test/transpile/`: Working directory for transpilation artifacts (not tracked by Git)
  - Not viewable on GitHub. Generate locally by running transpilation when needed.

## 6. Notes On Image Matching

- Image sample parity is judged by **exact output-file byte match** between Python and C++ execution outputs.
- PNG/GIF are treated uniformly; byte mismatch means mismatch (needs fix).

To run image parity checks automatically:

```bash
python3 tools/verify_sample_outputs.py --compile-flags="-O2"
```

- You can inspect both `stdout` diffs and image-file byte diffs together.
- For `sample/12_sort_visualizer` and `sample/16_glass_sculpture_chaos`, matching GIF frame blocks (delay values + LZW compressed data) has been confirmed.

If you want to ignore `stdout` diffs such as elapsed time and check image parity only:

```bash
python3 tools/verify_sample_outputs.py --ignore-stdout --compile-flags="-O2"
```

