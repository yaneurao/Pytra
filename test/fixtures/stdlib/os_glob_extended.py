from pytra.std import glob, os


def run_case() -> None:
    joined = os.path.join("alpha", "beta.txt")
    root, ext = os.path.splitext(joined)
    ok = True
    ok = ok and (os.path.basename(joined) == "beta.txt")
    ok = ok and (root == "alpha/beta")
    ok = ok and (ext == ".txt")
    ok = ok and (os.path.dirname(joined) == "alpha")
    ok = ok and os.path.exists("test/fixtures")
    ok = ok and (len(glob.glob("test/fixtures/core/*.py")) > 0)
    print(ok)


if __name__ == "__main__":
    run_case()
