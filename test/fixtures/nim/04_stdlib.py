
import math
from time import perf_counter

def stdlib_test():
    x = math.sqrt(16.0)
    y = math.fabs(-3.14)
    start = perf_counter()
    return (x, y, start)

if __name__ == "__main__":
    print(stdlib_test())
