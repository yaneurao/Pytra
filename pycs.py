#!/usr/bin/env python3
import argparse
import sys

from src.pycs_transpiler import TranspileError, transpile


def main() -> int:
    parser = argparse.ArgumentParser(description="Transpile typed Python code to C#")
    parser.add_argument("input", help="Path to input Python file")
    parser.add_argument("output", help="Path to output C# file")
    args = parser.parse_args()

    try:
        transpile(args.input, args.output)
    except (OSError, SyntaxError, TranspileError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
