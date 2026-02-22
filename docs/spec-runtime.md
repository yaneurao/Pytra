# Runtime Specification

<a href="../docs-jp/spec/spec-runtime.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>


### 1. Clarify Responsibility Split Between Generated Artifacts and Handwritten Implementations

- Auto-generated:
  - `runtime/cpp/pytra/std/<mod>.h`
  - `runtime/cpp/pytra/std/<mod>.cpp`
  - `runtime/cpp/pytra/utils/<mod>.h`
  - `runtime/cpp/pytra/utils/<mod>.cpp`
  - Examples: `runtime/cpp/pytra/std/json.h/.cpp`, `runtime/cpp/pytra/std/typing.h/.cpp`, `runtime/cpp/pytra/utils/assertions.h/.cpp`
  - `runtime/cpp/pytra/std/math.h` / `math.cpp` is generated from function signatures interpreted from `src/pytra/std/math.py` by `src/py2cpp.py`.
- Handwritten allowed:
  - `runtime/cpp/pytra/std/<mod>-impl.cpp`
  - `runtime/cpp/pytra/utils/<mod>-impl.cpp`
- Rules:
  - `<mod>.h/.cpp` are always regeneration targets (no manual edits).
  - `*-impl.cpp` is manually editable (excluded from regeneration).
  - `<mod>.cpp` delegates to functions in `*-impl.cpp`.
  - `src/py2cpp.py` is the single source-of-truth generator. Do not add per-module ad-hoc generators.
  - Use `py2cpp.py --emit-runtime-cpp` for generation to default runtime locations.

### 2. Fix Include Conventions

- Includes emitted for imports are fixed as follows:
  - `from pytra.std.glob import glob` -> `#include "pytra/std/glob.h"`
  - `from pytra.utils.gif import save_gif` -> `#include "pytra/utils/gif.h"`
- Transpiler must fix include paths to one convention and disallow mixing with legacy layouts.
- Additional rules:
  - Python import names and C++ include paths must be one-to-one.
  - Example: `import pytra.std.math` -> `#include "pytra/std/math.h"`
  - Example: `import pytra.utils.png` -> `#include "pytra/utils/png.h"`
  - Pass `src/runtime/cpp` as include root (`-I`) at compile time.
  - Canonical built-in foundation header: `runtime/cpp/pytra/built_in/py_runtime.h`
  - Mutual includes inside `runtime/cpp/pytra/built_in/*.h` must be same-directory relative (example: `#include "str.h"`).

#### 2.0 Guard Rule for `built_in` Headers

- Include guards in `runtime/cpp/pytra/built_in/*.h` must be derived from relative paths under `runtime/cpp/pytra/`.
  - Conversion rule: replace `/`, `.`, `-` with `_`, uppercase, and prepend `PYTRA_`.
  - Example: `runtime/cpp/pytra/built_in/list.h` -> `PYTRA_BUILT_IN_LIST_H`
  - Example: `runtime/cpp/pytra/built_in/py_runtime.h` -> `PYTRA_BUILT_IN_PY_RUNTIME_H`

#### 2.1 Module Name Mapping Rules (for User Modules)

Base rules:
- `pytra.std.<mod>` maps to `pytra::std::<mod>`.
- `pytra.utils.<mod>` maps to `pytra::utils::<mod>`.
- Include paths are derived by replacing `.` with `/` and appending `.h`.
- Only modules ending with `_impl` map `_impl -> -impl` in include paths.
- Namespace keeps `_impl` unchanged (never `-impl`).
- `.h` output is generated per module.
  - Output: `runtime/cpp/pytra/std/<mod>.h` or `runtime/cpp/pytra/utils/<mod>.h`
  - Top-level module functions become declarations (`.cpp` has definitions).
  - Top-level module constants/variables become `extern` declarations (`.cpp` has storage definitions).

Example 1: standard module (normal)

```python
import pytra.std.time as t

def now() -> float:
    return t.perf_counter()
```

```cpp
#include "pytra/std/time.h"

double now() {
    return pytra::std::time::perf_counter();
}
```

`pytra.std.time` header shape:

```cpp
// runtime/cpp/pytra/std/time.h
namespace pytra::std::time {
double perf_counter();
}  // namespace pytra::std::time
```

Example 2: runtime module (normal)

```python
import pytra.utils.png as png

def save(path: str, w: int, h: int, pixels: bytes) -> None:
    png.write_rgb_png(path, w, h, pixels)
```

```cpp
#include "pytra/utils/png.h"

void save(const str& path, int64 w, int64 h, const bytes& pixels) {
    pytra::utils::png::write_rgb_png(path, w, h, pixels);
}
```

Example 3: `_impl` module (special rule)

```python
import pytra.std.math_impl as _m

def root(x: float) -> float:
    return _m.sqrt(x)
```

```cpp
#include "pytra/std/math-impl.h"  // include uses -impl

float64 root(float64 x) {
    return pytra::std::math_impl::sqrt(x);  // namespace keeps _impl
}
```

Example 4: adding user-defined native module

```python
import pytra.std.foo_impl as _f

def f(x: float) -> float:
    return _f.calc(x)
```

```cpp
#include "pytra/std/foo-impl.h"

float64 f(float64 x) {
    return pytra::std::foo_impl::calc(x);
}
```

Module with constants has `extern` declarations in `.h`:

```cpp
// runtime/cpp/pytra/std/math.h
namespace pytra::std::math {
extern double pi;
extern double e;
double sqrt(double x);
}  // namespace pytra::std::math
```

#### 2.2 `.h/.cpp` Generation Flow from Python Input (Including Constants)

When the following Python module is passed to `py2cpp.py`, both `.h` and `.cpp` are generated.

```python
# src/pytra/std/math.py
import pytra.std.math_impl as _m

pi: float = _m.pi
e: float = _m.e

def sqrt(x: float) -> float:
    return _m.sqrt(x)
```

Generation commands (examples):

```bash
# Generate directly into default runtime path
python3 src/py2cpp.py src/pytra/std/math.py --emit-runtime-cpp

# Generate to arbitrary path
python3 src/py2cpp.py src/pytra/std/math.py \
  -o /tmp/math.cpp \
  --header-output /tmp/math.h \
  --top-namespace pytra::std::math
```

Generated `.h` example (constant declarations + function declarations):

```cpp
namespace pytra::std::math {

extern double pi;
extern double e;

double sqrt(double x);

}  // namespace pytra::std::math
```

Generated `.cpp` example (constant definitions + function definitions):

```cpp
#include "pytra/std/math-impl.h"

namespace pytra::std::math {

float64 pi = py_to_float64(pytra::std::math_impl::pi);
float64 e = py_to_float64(pytra::std::math_impl::e);

float64 sqrt(float64 x) {
    return py_to_float64(pytra::std::math_impl::sqrt(x));
}

}  // namespace pytra::std::math
```

Key points:
- Python module variable assignment (`pi = _m.pi`) is emitted as:
  - `.h`: `extern` declaration
  - `.cpp`: storage definition
- If import target is `_impl`, include uses `-impl.h` while namespace remains `_impl`.

### 3. Add Generation Spec for User Module Imports

- For `import mylib` / `from mylib import f`:
  - Generate `mylib.py` -> `mylib.h` / `mylib.cpp`.
- Dependency resolution:
  - Build import graph first, then generate in topological order.
  - Circular import is an error (`input_invalid`).
- Name conflict:
  - User modules colliding with `pytra.*` names are forbidden (`input_invalid`).

### 4. Fix ABI Boundary of `*-impl.cpp`

- Functions in `*-impl.cpp` must be limited to C++-dependent minimal primitives.
  - Examples: filesystem, regex, clock, process, OS APIs
- All other logic (formatting, conversion, validation) remains in Python source-of-truth (`src/pytra/utils/*.py`).
- This confines cross-language differences to the `*-impl` layer.

### 5. Minimal Rules for Generation Templates

- Generated `<mod>.h`:
  - Public API declarations only
  - Include guard and namespace definitions
  - Generated from EAST via `py2cpp.py --header-output` (no manual edits)
- Generated `<mod>.cpp`:
  - `#include "<mod>.h"`
  - Do not include `#include "<mod>-impl.cpp"`; use link-time resolution via declarations
  - Contains transpiled Python logic and `*-impl` calls
  - Generated with `py2cpp.py -o <mod>.cpp` (no manual edits)
  - `pytra.utils.png` / `pytra.utils.gif` use bridge style:
    - Transpiled body goes under `namespace ...::generated`
    - Public APIs (`write_rgb_png`, `save_gif`, `grayscale_palette`) are exposed through bridge wrappers with type conversion

- Reserved naming:
  - If Python module name ends with `_impl`, map to `-impl` in C++ header path.
  - Example: `import pytra.std.math_impl` -> `#include "pytra/std/math-impl.h"`

### 6. Include Test Requirements in Specification

Each module must satisfy at least:
1. Python execution result matches C++ execution result.
2. Both import forms pass for modules under `runtime/cpp/pytra/std` and `runtime/cpp/pytra/utils` (`import` and `from ... import ...`).
3. Outputs are stable when regenerated from scratch (reproducibility).

### 7. Naming for Future Multi-language Expansion

- Keep C++-specific concept (`-impl.cpp`) and map to equivalent layer names in other languages.
  - Example: `-impl.cs`, `-impl.rs`
- In specification text, define this as an abstract "native implementation layer (impl layer)".

### 8. Fix Current Layout as Canonical

- Canonical C++ runtime implementation location is `runtime/cpp/pytra/std/*` and `runtime/cpp/pytra/utils/*`.
- Includes are fixed to reference these paths directly for now.
- If layout is changed in the future, update this spec first, then implementation.

### 9. Naming Policy

- Library hierarchy is unified into two families:
  - `pytra.std`: replacement for Python standard library
  - `pytra.utils`: Pytra-specific runtime helpers
- Avoid ambiguous names like plain `utils`; prefer names that describe responsibility.

### 10. Conversion Policy for `pytra.*` Modules (Do Not Ignore)

- Treat `pytra.std.*` / `pytra.utils.*` as normal Python modules.
  - Do not ignore `import`, module variable assignments, or function bodies by folder-name heuristics.
  - Example: `pi = _m.pi` and `def sqrt(...): return _m.sqrt(...)` are semantically meaningful.
- Replacement with native implementation is allowed only at explicit boundaries.
  - Delegate generated artifacts (example: `runtime/cpp/pytra/std/math.h/.cpp`) to handwritten implementations (`py_math.h/.cpp` or `*-impl.cpp`).
  - Implicit rules such as "ignore everything except function signatures in this folder" are prohibited.
- Apply identical conversion rules to official modules and user-authored modules.
  - Official modules must not be special-cased in ways users cannot reproduce.

### 11. C++ Mapping for Constants and Functions

- C++ generation keeps Python module definitions and maps to native functions where required.
- Example (`pytra.std.math`):
  - `pi = _m.pi` maps to:
    - `.h`: `extern double pi;`
    - `.cpp`: `float64 pi = py_to_float64(pytra::std::math_impl::pi);`
  - `return _m.sqrt(x)` maps to `pytra::std::math_impl::sqrt(x)`.
- Provide mapping targets (`pytra::std::<name>_impl::*`) as handwritten implementations in advance; generated code references them.
