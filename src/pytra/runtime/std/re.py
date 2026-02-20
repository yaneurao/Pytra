from __future__ import annotations


def _is_space(ch: str) -> bool:
    return ch == " " or ch == "\t" or ch == "\n" or ch == "\r" or ch == "\f" or ch == "\v"


def sub(pattern: str, repl: str, text: str) -> str:
    if pattern == r"\s+":
        out: list[str] = []
        i = 0
        n = len(text)
        while i < n:
            ch = text[i]
            if _is_space(ch):
                while i < n and _is_space(text[i]):
                    i += 1
                out.append(repl)
                continue
            out.append(ch)
            i += 1
        return "".join(out)
    return text.replace(pattern, repl)
