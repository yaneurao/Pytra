def count_vowels(s: str) -> int:
    count: int = 0
    for ch in s:
        if ch == "a" or ch == "e" or ch == "i" or ch == "o" or ch == "u":
            count += 1
    return count

if __name__ == "__main__":
    print(count_vowels("hello world"))
    print(count_vowels("aeiou"))
