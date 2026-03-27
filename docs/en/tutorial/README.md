<a href="../../ja/tutorial/README.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# Tutorial

A starting point for first-time Pytra users.

## Get Running in 3 Minutes

```python
def add(a: int, b: int) -> int:
    return a + b

if __name__ == "__main__":
    print(add(3, 4))
```

Transpile this `add.py` to C++ and run it:

```bash
./pytra add.py --output-dir out/add_case --build --run --exe add.out
```

Output:

```text
7
```

To transpile to Rust instead:

```bash
./pytra add.py --target rs --output-dir out/rs_case
```

## Reading Order

1. [How to use](./how-to-use.md) — Execution steps, options, input constraints
2. [Architecture](./architecture.md) — Pipeline overview and the role of each stage
3. [Python compatibility guide](../spec/spec-python-compat.md) — Differences from Python, unsupported syntax
4. [Troubleshooting](./troubleshooting.md) — When you get stuck
5. [Union types and isinstance narrowing](./union-and-narrowing.md) — Handling multiple types and automatic type refinement
6. [Traits (interfaces)](./trait.md) — Attaching multiple behavioral contracts to a type

That should be enough to use Pytra. The following are for when you need them:

7. [Advanced usage](./advanced-usage.md) — `@extern`, `@abi`, `@template`, nominal ADT, etc.
8. [Specification index](../spec/index.md) — The source of truth for language specifications
9. [Development operations guide](./dev-operations.md) — Parity check, local CI (for developers)

## Related Links

- [Specification index](../spec/index.md)
- [pylib module list](../spec/spec-pylib-modules.md)
- [Sample list](../../sample/README.md)
