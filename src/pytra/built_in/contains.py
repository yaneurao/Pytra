"""Pure-Python source-of-truth for containment helpers."""


def py_contains_dict_object(values: object, key: object) -> bool:
    needle = str(key)
    for cur in values:
        if cur == needle:
            return True
    return False


def py_contains_list_object(values: object, key: object) -> bool:
    for cur in values:
        if cur == key:
            return True
    return False


def py_contains_set_object(values: object, key: object) -> bool:
    for cur in values:
        if cur == key:
            return True
    return False


def py_contains_str_object(values: object, key: object) -> bool:
    needle = str(key)
    n = len(values)
    m = len(needle)
    if m == 0:
        return True
    i = 0
    last = n - m
    while i <= last:
        j = 0
        ok = True
        while j < m:
            if values[i + j] != needle[j]:
                ok = False
                break
            j += 1
        if ok:
            return True
        i += 1
    return False
