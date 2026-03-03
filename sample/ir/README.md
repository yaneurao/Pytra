# sample/ir

`sample/py` 由来の EAST3(JSON) fixture です。

- `ir2lang.py` の backend-only 回帰で利用します。
- 形式は `docs/ja/plans/p1-ir2lang-lazy-backend-from-east3.md` の受理契約に従います。
- 更新例:
  - `python3 src/py2x.py sample/py/01_mandelbrot.py --target cpp -o out/ir_seed.cpp --dump-east3-after-opt sample/ir/01_mandelbrot.east3.json`
