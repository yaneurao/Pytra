# 03: ジュリア集合を PNG 形式で出力するサンプルです。
# トランスパイル互換を意識し、単純なループ中心で実装しています。

from time import perf_counter
import png_helper


def render_julia(width: int, height: int, max_iter: int, cx: float, cy: float) -> bytearray:
    pixels: bytearray = bytearray()

    y: int = 0
    while y < height:
        zy0: float = -1.2 + 2.4 * ((y * 1.0) / ((height - 1) * 1.0))

        x: int = 0
        while x < width:
            zx: float = -1.8 + 3.6 * ((x * 1.0) / ((width - 1) * 1.0))
            zy: float = zy0

            i: int = 0
            while i < max_iter:
                zx2: float = zx * zx
                zy2: float = zy * zy
                if zx2 + zy2 > 4.0:
                    break
                zy = 2.0 * zx * zy + cy
                zx = zx2 - zy2 + cx
                i = i + 1

            r: int = 0
            g: int = 0
            b: int = 0
            if i >= max_iter:
                r = 0
                g = 0
                b = 0
            else:
                t: float = (i * 1.0) / (max_iter * 1.0)
                r = int(255.0 * (0.2 + 0.8 * t))
                g = int(255.0 * (0.1 + 0.9 * (t * t)))
                b = int(255.0 * (1.0 - t))

            pixels.append(r)
            pixels.append(g)
            pixels.append(b)
            x = x + 1

        y = y + 1

    return pixels


def run_julia() -> None:
    width: int = 1280
    height: int = 720
    max_iter: int = 520
    out_path: str = "sample/out/julia_03.png"

    start: float = perf_counter()
    pixels: bytearray = render_julia(width, height, max_iter, -0.8, 0.156)
    png_helper.write_rgb_png(out_path, width, height, pixels)
    elapsed: float = perf_counter() - start

    print("output:", out_path)
    print("size:", width, "x", height)
    print("max_iter:", max_iter)
    print("elapsed_sec:", elapsed)


if __name__ == "__main__":
    run_julia()
