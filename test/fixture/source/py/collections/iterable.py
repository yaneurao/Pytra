

from pytra.utils.assertions import py_assert_stdout
def main():

    l : list[int] = [1, 2, 3]
    sum = 0
    for v in l:
        sum += v
    print(sum)


def _case_main() -> None:
    main()

if __name__ == "__main__":
    print(py_assert_stdout(['6'], _case_main))
