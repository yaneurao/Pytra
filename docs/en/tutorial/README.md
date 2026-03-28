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
2. [Troubleshooting](./troubleshooting.md) — When you get stuck
3. [Try the samples](./samples.md) — Try the 18 sample programs
4. [Exception handling](./exception.md) — raise / try / except / finally
5. [Traits (interfaces)](./trait.md) — Attaching multiple behavioral contracts to a type
6. [Union types and isinstance narrowing](./union-and-narrowing.md) — Handling multiple types and automatic type refinement
7. [Differences from Python](./python-differences.md) — Type annotations, imports, unsupported syntax

That should be enough to use Pytra. The following are for when you need them:

8. [pylib module list](../spec/spec-pylib-modules.md) — Available modules and functions
9. [Architecture](./architecture.md) — Pipeline overview and the role of each stage
10. [Advanced usage](./advanced-usage.md) — `@extern`, `@abi`, `@template`, nominal ADT, etc.
11. [Specification index](../spec/index.md) — The source of truth for language specifications
12. [Development operations guide](./dev-operations.md) — Parity check, local CI (for developers)
