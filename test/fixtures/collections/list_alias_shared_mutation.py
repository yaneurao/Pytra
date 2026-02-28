# This file contains test/implementation code for list alias shared mutation.
# Python contract: alias b shares the same list object as a.


def run_alias_list_mutation() -> bool:
    a: list[int] = [1, 2]
    b = a
    b.append(3)
    ok_after_append = len(a) == 3
    b.pop()
    ok_after_pop = len(a) == 2
    return ok_after_append and ok_after_pop


if __name__ == "__main__":
    print(run_alias_list_mutation())
