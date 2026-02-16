# case30: スライス構文 a[b:c] の基本テスト（stepなし）。

def main() -> None:
    nums: list[int] = [10, 20, 30, 40, 50]
    text: str = "abcdef"

    mid_nums: list[int] = nums[1:4]
    mid_text: str = text[2:5]

    print(mid_nums[0])
    print(mid_nums[2])
    print(mid_text)


if __name__ == "__main__":
    main()
