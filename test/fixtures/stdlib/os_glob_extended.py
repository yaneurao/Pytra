from pytra.std import glob, os


def run_case() -> None:
    joined = os.path.join("alpha", "beta.txt")
    root, ext = os.path.splitext(joined)
    ok = True
    ok = ok and (os.path.basename(joined) == "beta.txt")
    ok = ok and (root == "alpha/beta")
    ok = ok and (ext == ".txt")
    ok = ok and (os.path.dirname(joined) == "alpha")
    # 実行 cwd 依存にならないよう、必ず存在する相対パスで確認する。
    ok = ok and os.path.exists(".")
    ok = ok and (len(glob.glob("*.cpp")) > 0)
    print(ok)


if __name__ == "__main__":
    run_case()
