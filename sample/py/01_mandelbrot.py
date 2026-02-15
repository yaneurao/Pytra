# 01: マンデルブロ集合を PNG 画像として出力するサンプルです。
# 将来のトランスパイルを意識して、構文はなるべく素直に書いています。

from time import perf_counter
import png_helper


def escape_count(cx: float, cy: float, max_iter: int) -> int:
    """1点 (cx, cy) の発散までの反復回数を返す。"""
    x: float = 0.0
    y: float = 0.0
    i: int = 0
    while i < max_iter:
        x2: float = x * x
        y2: float = y * y
        if x2 + y2 > 4.0:
            return i
        y = 2.0 * x * y + cy
        x = x2 - y2 + cx
        i = i + 1
    return max_iter


def color_map(iter_count: int, max_iter: int) -> tuple[int, int, int]:
    """反復回数を RGB に変換する。"""
    if iter_count >= max_iter:
        return (0, 0, 0)

    # 簡単なグラデーション（青系 -> 黄系）
    t: float = (iter_count * 1.0) / (max_iter * 1.0)
    r: int = int(255.0 * (t * t))
    g: int = int(255.0 * t)
    b: int = int(255.0 * (1.0 - t))
    return (r, g, b)


def render_mandelbrot(
    width: int,
    height: int,
    max_iter: int,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
) -> bytearray:
    """マンデルブロ画像の RGB バイト列を生成する。"""
    pixels: bytearray = bytearray()

    y: int = 0
    while y < height:
        py: float = y_min + (y_max - y_min) * ((y * 1.0) / ((height - 1) * 1.0))

        x: int = 0
        while x < width:
            px: float = x_min + (x_max - x_min) * ((x * 1.0) / ((width - 1) * 1.0))
            it: int = escape_count(px, py, max_iter)
            r: int
            g: int
            b: int
            if it >= max_iter:
                r = 0
                g = 0
                b = 0
            else:
                t: float = (it * 1.0) / (max_iter * 1.0)
                r = int(255.0 * (t * t))
                g = int(255.0 * t)
                b = int(255.0 * (1.0 - t))
            pixels.append(r)
            pixels.append(g)
            pixels.append(b)
            x = x + 1

        y = y + 1

    return pixels


def run_mandelbrot() -> None:
    width: int = 800
    height: int = 600
    max_iter: int = 400
    out_path: str = "sample/out/mandelbrot_01.png"

    start: float = perf_counter()

    pixels: bytearray = render_mandelbrot(
        width,
        height,
        max_iter,
        -2.2,
        1.0,
        -1.2,
        1.2,
    )
    png_helper.write_rgb_png(out_path, width, height, pixels)

    elapsed: float = perf_counter() - start
    print("output:", out_path)
    print("size:", width, "x", height)
    print("max_iter:", max_iter)
    print("elapsed_sec:", elapsed)


if __name__ == "__main__":
    run_mandelbrot()
