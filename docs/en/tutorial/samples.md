<a href="../../ja/tutorial/samples.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# Try the Samples

Pytra comes with 18 sample programs: fractal images, ray tracing, Game of Life, sort visualization, a mini language interpreter, and more.

## Run One

Transpile the Mandelbrot set to C++ and run it:

```bash
./pytra sample/py/01_mandelbrot.py --output-dir out/mandelbrot --build --run --exe mandelbrot.out
```

A PNG image is generated.

To transpile to Go instead:

```bash
./pytra sample/py/01_mandelbrot.py --target go --output-dir out/mandelbrot_go
```

## Sample List

| No | Description | Output |
|---|---|---|
| 01 | Mandelbrot set | PNG |
| 02 | Ray tracing (spheres) | PNG |
| 03 | Julia set | PNG |
| 04 | Orbit trap Julia | PNG |
| 05 | Mandelbrot zoom | GIF |
| 06 | Julia set parameter sweep | GIF |
| 07 | Game of Life | GIF |
| 08 | Langton's ant | GIF |
| 09 | Fire simulation | GIF |
| 10 | Plasma effect | GIF |
| 11 | Lissajous particles | GIF |
| 12 | Sort visualization | GIF |
| 13 | Maze generation | GIF |
| 14 | Raymarching light cycle | GIF |
| 15 | Wave interference | GIF |
| 16 | Glass sculpture chaos rotation | GIF |
| 17 | Monte Carlo pi estimation | Text |
| 18 | Mini language interpreter | Text |

Output examples:

<table><tr>
<td width="50%">

![01_mandelbrot](../../../sample/images/01_mandelbrot.png)

01: Mandelbrot set

</td>
<td width="50%">

![07_game_of_life_loop](../../../sample/images/07_game_of_life_loop.gif)

07: Game of Life

</td>
</tr></table>

## Compare the Transpiled Code

Compare the Python source with the transpiled output:

```bash
# Python source
cat sample/py/01_mandelbrot.py

# Transpiled to C++
cat sample/cpp/01_mandelbrot.cpp

# Transpiled to Go
cat sample/go/01_mandelbrot.go
```

You'll see that the structure of the original Python code is preserved almost exactly.

## Regenerate All Samples

```bash
python3 tools/regenerate_samples.py
```

This transpiles all 18 samples to all 18 languages.

## Speed Comparison

Execution time comparison between Python and transpiled C++:

| No | Description | Python | C++ | Speedup |
|---|---|---|---|---|
| 06 | Julia set parameter sweep | 9.6s | 0.5s | ~19x |
| 16 | Glass sculpture chaos rotation | 6.8s | 0.3s | ~23x |

For full benchmarks across all languages and samples, see the [detailed sample list](../../../sample/README.md).

## Source Code

All Python sources are in `sample/py/`. Transpiled results are in `sample/cpp/`, `sample/go/`, `sample/rs/`, etc.
