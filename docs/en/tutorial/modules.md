<a href="../../ja/tutorial/modules.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# Available Modules

In Pytra, you use `pytra.std.*` instead of the Python standard library. This page introduces the most commonly used modules with examples.

## math — Math functions

```python
from pytra.std import math

x: float = math.sqrt(2.0)
y: float = math.sin(math.pi / 4.0)
z: float = math.floor(3.7)    # 3.0
```

Available functions: `sqrt`, `sin`, `cos`, `tan`, `exp`, `log`, `log10`, `fabs`, `floor`, `ceil`, `pow`

Constants: `math.pi`, `math.e`

## pathlib — File path operations

```python
from pytra.std.pathlib import Path

p: Path = Path("data/output")
p.mkdir(parents=True, exist_ok=True)

text: str = Path("input.txt").read_text()
Path("output.txt").write_text("hello")

name: str = Path("image.png").stem      # "image"
ext: str = Path("image.png").suffix     # ".png"
```

## json — JSON read/write

```python
from pytra.std import json

data: str = json.dumps({"name": "pytra", "version": 1})
# → '{"name": "pytra", "version": 1}'

obj = json.loads('{"x": 42}')
```

## time — Time measurement

```python
from pytra.std.time import perf_counter

start: float = perf_counter()
# ... processing ...
elapsed: float = perf_counter() - start
print("elapsed: " + str(elapsed) + " sec")
```

## sys — Command line arguments

```python
from pytra.std import sys

for arg in sys.argv:
    print(arg)
```

## os — File system operations

```python
from pytra.std import os

cwd: str = os.getcwd()
os.makedirs("output/images", exist_ok=True)
full: str = os.path.join("data", "file.txt")
```

## random — Random numbers

```python
from pytra.std import random

random.seed(42)
x: float = random.random()          # 0.0 to 1.0
n: int = random.randint(1, 100)     # 1 to 100
```

## Image output — PNG / GIF

Pytra includes transpilable image writing helpers.

```python
from pytra.utils.png import write_rgb_png
from pytra.utils.gif import save_gif

# Write a 256x256 RGB image
pixels: list[int] = [0] * (256 * 256 * 3)
# ... write colors to pixels ...
write_rgb_png("output.png", 256, 256, pixels)
```

Many samples use these helpers to generate PNG/GIF images.

## argparse — Command line argument parsing

```python
from pytra.std import argparse

parser: argparse.ArgumentParser = argparse.ArgumentParser()
parser.add_argument("--name", default="world")
parser.add_argument("--count", type=int, default=1)
args: argparse.Namespace = parser.parse_args()

i: int = 0
while i < args.count:
    print("hello " + args.name)
    i += 1
```

## glob — File pattern matching

```python
from pytra.std import glob

files: list[str] = glob.glob("data/*.txt")
for f in files:
    print(f)
```

## re — Regular expressions

```python
from pytra.std import re

m: re.Match = re.match("([0-9]+)", "abc123def")
if m is not None:
    print(m.group(1))  # "123"

result: str = re.sub("[0-9]+", "NUM", "abc123def456")
print(result)  # "abcNUMdefNUM"
```

## enum — Enumerations

```python
from pytra.std.enum import IntEnum

class Color(IntEnum):
    RED = 0
    GREEN = 1
    BLUE = 2

c: Color = Color.RED
print(c)  # 0
```

`Enum`, `IntEnum`, and `IntFlag` are available.

## timeit — Simple timer

```python
from pytra.std import timeit

start: float = timeit.default_timer()
# ... processing ...
elapsed: float = timeit.default_timer() - start
print(str(elapsed) + " sec")
```

Similar to `perf_counter()`, for when you prefer the `timeit` module interface.

## Full module list

For the complete list of all modules and functions, see the [pylib module list (spec)](../spec/spec-pylib-modules.md).
