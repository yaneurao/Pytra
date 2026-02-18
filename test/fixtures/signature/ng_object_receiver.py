# object receiver access test: attribute/method access on `object` is rejected.

def bad_attr(x: object) -> int:
    return x.bit_length()

if __name__ == "__main__":
    print(bad_attr(3))
