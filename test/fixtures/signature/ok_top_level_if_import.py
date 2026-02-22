# self_hosted parser: top-level if with import in block.

x: int = 1
if x > 0:
    import math
    x = x + 1

