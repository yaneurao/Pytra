<a href="../../en/tutorial/modules.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# 使えるモジュール

Pytra では Python 標準ライブラリの代わりに `pytra.std.*` を使います。このページでは、よく使うモジュールを実例付きで紹介します。

## math — 数学関数

```python
from pytra.std import math

x: float = math.sqrt(2.0)
y: float = math.sin(math.pi / 4.0)
z: float = math.floor(3.7)    # 3.0
```

使える関数: `sqrt`, `sin`, `cos`, `tan`, `exp`, `log`, `log10`, `fabs`, `floor`, `ceil`, `pow`

定数: `math.pi`, `math.e`

## pathlib — ファイルパス操作

```python
from pytra.std.pathlib import Path

p: Path = Path("data/output")
p.mkdir(parents=True, exist_ok=True)

text: str = Path("input.txt").read_text()
Path("output.txt").write_text("hello")

name: str = Path("image.png").stem      # "image"
ext: str = Path("image.png").suffix     # ".png"
```

## json — JSON の読み書き

```python
from pytra.std import json

data: str = json.dumps({"name": "pytra", "version": 1})
# → '{"name": "pytra", "version": 1}'

obj = json.loads('{"x": 42}')
```

## time — 時間計測

```python
from pytra.std.time import perf_counter

start: float = perf_counter()
# ... 処理 ...
elapsed: float = perf_counter() - start
print("elapsed: " + str(elapsed) + " sec")
```

## sys — コマンドライン引数

```python
from pytra.std import sys

for arg in sys.argv:
    print(arg)
```

## os — ファイルシステム操作

```python
from pytra.std import os

cwd: str = os.getcwd()
os.makedirs("output/images", exist_ok=True)
full: str = os.path.join("data", "file.txt")
```

## random — 乱数

```python
from pytra.std import random

random.seed(42)
x: float = random.random()          # 0.0 〜 1.0
n: int = random.randint(1, 100)     # 1 〜 100
```

## 画像出力 — PNG / GIF

Pytra にはトランスパイル可能な画像書き出しヘルパーが付属しています。

```python
from pytra.utils.png import write_rgb_png
from pytra.utils.gif import save_gif

# 幅 256 x 高さ 256 の RGB 画像を書き出す
pixels: list[int] = [0] * (256 * 256 * 3)
# ... pixels に色を書き込む ...
write_rgb_png("output.png", 256, 256, pixels)
```

サンプルの多くがこのヘルパーを使って PNG/GIF を生成しています。

## argparse — コマンドライン引数の解析

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

## glob — ファイルパターン検索

```python
from pytra.std import glob

files: list[str] = glob.glob("data/*.txt")
for f in files:
    print(f)
```

## re — 正規表現

```python
from pytra.std import re

m: re.Match = re.match("([0-9]+)", "abc123def")
if m is not None:
    print(m.group(1))  # "123"

result: str = re.sub("[0-9]+", "NUM", "abc123def456")
print(result)  # "abcNUMdefNUM"
```

## enum — 列挙型

```python
from pytra.std.enum import IntEnum

class Color(IntEnum):
    RED = 0
    GREEN = 1
    BLUE = 2

c: Color = Color.RED
print(c)  # 0
```

`Enum`, `IntEnum`, `IntFlag` が使えます。

## timeit — 簡易タイマー

```python
from pytra.std import timeit

start: float = timeit.default_timer()
# ... 処理 ...
elapsed: float = timeit.default_timer() - start
print(str(elapsed) + " sec")
```

`perf_counter()` と同様ですが、`timeit` モジュール経由で使いたい場合に。

## 全モジュール一覧

全モジュール・全関数の完全な一覧は [pylib モジュール一覧（仕様書）](../spec/spec-pylib-modules.md) を参照してください。
