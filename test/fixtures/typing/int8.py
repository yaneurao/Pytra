

from pylib.tra.assertions import py_assert_stdout
def main():

    i : int8 = 1
    print(i * 2)


def _case_main() -> None:
    main()

if __name__ == "__main__":
    print(py_assert_stdout(['2'], _case_main))
