# 04: 整数演算のみで大きなグリッドを走査し、チェックサムを計算するサンプルです。
# 浮動小数点誤差の影響を避け、言語間で比較しやすいベンチマークにします。

from time import perf_counter


def run_integer_grid_checksum(width: int, height: int, seed: int) -> int:
    mod_main: int = 2147483647
    mod_out: int = 1000000007
    acc: int = seed % mod_out

    for y in range(height):
        row_sum: int = 0
        for x in range(width):
            v: int = (x * 37 + y * 73 + seed) % mod_main
            v = (v * 48271 + 1) % mod_main
            row_sum += v % 256
        acc = (acc + row_sum * (y + 1)) % mod_out

    return acc


def run_integer_benchmark() -> None:
    width: int = 2400
    height: int = 1600

    start: float = perf_counter()
    checksum: int = run_integer_grid_checksum(width, height, 123456789)
    elapsed: float = perf_counter() - start

    print("pixels:", width * height)
    print("checksum:", checksum)
    print("elapsed_sec:", elapsed)


if __name__ == "__main__":
    run_integer_benchmark()
