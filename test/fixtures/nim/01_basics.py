
def add(a: int, b: int) -> int:
    return a + b

def loop_test(n: int) -> int:
    res = 0
    for i in range(n):
        if i % 2 == 0:
            res += i
        else:
            res -= 1
    return res

if __name__ == "__main__":
    print(add(1, 2))
    print(loop_test(10))
