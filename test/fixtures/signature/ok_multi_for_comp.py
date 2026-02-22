# self_hosted parser: list comprehension with multiple for clauses.

rows: list[list[int]] = [[1, 2], [3]]
flat: list[int] = [x for row in rows for x in row]

