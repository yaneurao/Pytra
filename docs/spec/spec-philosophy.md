<a href="../../docs-jp/spec/spec-philosophy.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# Development Philosophy

Pytra is a transpiler designed for running one logic base across multiple languages without unnecessary friction.

In multi-platform development, different languages are typically chosen for different use cases.  
When the same specification is reimplemented and maintained in multiple languages, costs increase, and so do risks of spec drift and bug injection.  
To reduce this duplication, Pytra takes the approach: write core logic in Python, then transpile to the required languages.

## Why Python AST Alone Is Not Enough

Python's standard `ast` is useful as a syntax tree, but it lacks information needed for practical transpilation.
Main gaps include:

- It does not retain comments, blank lines, or original layout information, making it hard to reproduce output close to source code.
- Standard AST itself does not retain inferred types for omitted annotations, or required cast information.
- Preprocessing such as `range` normalization, name-collision avoidance, and main-guard extraction tends to be duplicated across backends.
- Semantic information useful for optimization (such as readonly/mutable argument semantics) is hard to pass as shared data.

If each language backend fills these gaps independently, preprocessing logic fragments, and behavior divergence plus maintenance cost increase.  
To avoid this, Pytra introduces a layer that finalizes shared semantics after AST.

## EAST-Centric Design

EAST (Extended AST) is an extended abstract syntax tree designed specifically for Pytra.  
It is not an adopted general standard; it is defined to fill the gaps above.

EAST does not replace Python AST. It is a post-AST layer that enriches semantic information.

- Commonization: Finalize type inference, explicit casts, `range` normalization, name-collision avoidance, etc. during EAST construction.
- Separation of responsibilities: Backends (e.g., C++) focus on mapping EAST into target languages.
- Safety: If inference cannot be determined uniquely, stop with an error instead of generating ambiguous output.
- Maintainability: Keep source intent (names, comments, blank lines, structure) as much as possible in generated code.

This policy reduces language-specific diff implementations and enables both specification consistency and performance improvements.

For implementation-aligned EAST details, see [EAST Specification (Implementation-Aligned)](spec-east.md).

## What We Prioritize

- Readability: Generated code should stay readable, preserving variable names, comments, blank lines, and structure as much as possible.
- Performance: Transpile Python implementations to C++/Rust, etc., to approach practical runtime speed.
- Ease of verification: Prioritize structures that make Python output vs. transpiled output comparisons easy.
- Extensibility: Through EAST, make it possible to incrementally expand supported syntax, optimizations, and target languages.

## Performance Stance

Pytra is not "Python stays slow forever"; it is designed to move toward native execution when needed.  
The ultimate target is transpilation quality close to handwritten C++ performance.

However, designs that sacrifice readability or traceability only for speed are avoided.  
Optimization is advanced incrementally, assuming long-term operation, maintenance, and debugging.

## Basic Development/Operation Policy

- Prioritize correctness first, then apply optimizations.
- Make transpilation rules as explicit as possible to improve reproducibility.
- Use selfhost (transpiling the transpiler itself) to continuously expose design weaknesses.

With this philosophy, Pytra aims to be not just a code generator, but a practical foundation for multi-language operations.
