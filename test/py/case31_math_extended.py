# このファイルは `test/py/case31_math_extended.py` のテスト/実装コードです。
# math モジュール拡張関数（tan, log, log10 など）の回帰確認に使います。
# 各言語ランタイムで同じ丸め結果になることを期待します。

import math


def main() -> None:
    # 三角関数の確認（π/4 の tan は 1 に近い）。
    tan_v: float = math.tan(math.pi / 4.0)

    # 対数関数の確認。
    log_v: float = math.log(100.0)
    log10_v: float = math.log10(1000.0)

    # 絶対値・切り上げ・べき乗の確認。
    fabs_v: float = math.fabs(-12.5)
    ceil_v: float = math.ceil(2.01)
    pow_v: float = math.pow(3.0, 4.0)

    # 変換後言語との差を吸収するため、小数は丸めて比較しやすく出力する。
    print(round(tan_v, 6))
    print(round(log_v, 6))
    print(round(log10_v, 6))
    print(round(fabs_v, 6))
    print(round(ceil_v, 6))
    print(round(pow_v, 6))


if __name__ == "__main__":
    main()
