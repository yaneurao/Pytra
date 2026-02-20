# case30: スライス構文 a[b:c] の基本テスト（stepなし）。


from pytra.utils.assertions import py_assert_stdout
def main() -> None:
    nums: list[int] = [10, 20, 30, 40, 50]
    text: str = "abcdef"

    mid_nums: list[int] = nums[1:4]
    mid_text: str = text[2:5]

    print(mid_nums[0])
    print(mid_nums[2])
    print(mid_text)


def _case_main() -> None:
    main()

if __name__ == "__main__":
    print(py_assert_stdout(['20', '40', 'cde'], _case_main))
