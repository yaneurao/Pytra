<a href="../../ja/plans/p7-go-selfhost-runtime.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-%E6%97%A5%E6%9C%AC%E8%AA%9E-2563EB?style=flat-square">
</a>

# P7-GO-SELFHOST-RUNTIME: Actually run the Go selfhost binary and achieve parity PASS

Last updated: 2026-03-31
Status: Not started

## Background

P6-GO-SELFHOST passed `go build`, but there are still gaps before the selfhost binary can actually convert fixture/sample/stdlib and produce correct output. The ultimate goal is parity PASS with `run_selfhost_parity.py --selfhost-lang go`.

## Known issues (analysis by the Go team)

### 1. linker type_id assignment failure

The type hierarchy for classes that have external base classes, such as `CommonRenderer(ABC)`, cannot be resolved for type_id. External classes should fall back to `object`.

### 2. Go emitter's own Go translation is not in golden

`test/selfhost/go/` intentionally excludes `emit/go/` (to avoid circular dependency). However, if the Go translation of `emit_go_module` is not included in the selfhost binary, the Go selfhost compiler cannot emit Go code.

Workarounds for the circular dependency:
- Separate the Go translation of the Go emitter into a different package and link it at selfhost build time
- Or include the translation of `emit/go/` in golden and combine all files at build time

### 3. main() is empty

The Go-translated `main()` does not have the CLI logic of Python's `pytra-cli2`. A minimal CLI wrapper that reads EAST3 JSON and emits code is needed.

```go
// main.go (minimal CLI wrapper)
func main() {
    input := os.Args[1]
    east3 := loadEAST3(input)
    code := emit_go_module(east3)
    fmt.Print(code)
}
```

## Flow

1. Fix the linker — type_id fallback for external classes
2. Include the Go translation of the Go emitter in selfhost
3. Add a CLI wrapper
4. Verify with `run_selfhost_parity.py --selfhost-lang go`

## Verification method

```bash
python3 tools/run/run_selfhost_parity.py --selfhost-lang go
```

PASS condition: for all fixture + sample + stdlib cases, the execution result of code emitted by the selfhost Go binary must match Python.

## Decision Log

- 2026-03-31: Analysis after P6 completion revealed 3 gaps. Decided that the Go team will address them.
