# P0: Implement Ruby Image Output Runtime and Recover Byte Parity

Last updated: 2026-02-28

Related TODO:
- `ID: P0-RUBY-IMAGE-PARITY-01` in `docs/ja/todo/index.md`

Background:
- `sample/ruby/01_mandelbrot.rb` calls `__pytra_noop(...)` at image-save points, so PNG is not actually output.
- `__pytra_noop` in `src/runtime/ruby/pytra/py_runtime.rb` is a no-op implementation, so image files are not generated.
- As a result, `runtime_parity_check` (stdout comparison) can pass, but image artifact parity is not established.

Goal:
- Implement a runtime for the Ruby backend that actually writes PNG/GIF, and recover byte-level agreement with Python execution results for image samples including `sample/01`.

In scope:
- `src/runtime/ruby/pytra/py_runtime.rb` (concrete implementation of image-output helpers)
- Lowering of image-save calls in Ruby emitter (remove `__pytra_noop` path)
- Regenerate `sample/ruby`
- Artifact parity verification path for image outputs (at least `sample/01` PNG)

Out of scope:
- Global performance optimization for the Ruby backend
- Full redesign of runtime helpers outside image output
- Image runtime changes for other language backends

Acceptance criteria:
- Running Ruby actually generates PNG for `sample/01`.
- For `sample/01`, PNG bytes from Python execution and Ruby execution are identical.
- A representative GIF case (`sample/06`, etc.) also confirms Python/Ruby GIF byte equality (or differences are formalized as spec rationale).
- `runtime_parity_check --targets ruby --all-samples` passes without regression.

Verification commands (planned):
- `python3 tools/check_todo_priority.py`
- `python3 tools/runtime_parity_check.py --case-root sample --targets ruby --all-samples --ignore-unstable-stdout`
- `python3 tools/regenerate_samples.py --langs ruby --force`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2rb_smoke.py' -v`
- `python3 tools/check_py2rb_transpile.py`

Decision log:
- 2026-02-28: Per user instruction, created a P0 plan that prioritizes fixing the no-op Ruby image-output path.
- 2026-02-28: Adopted implementation policy to switch Ruby emitter lowering for `save_gif` / `write_rgb_png` / `grayscale_palette` from `__pytra_noop` / `[]` to concrete runtime calls, and map `save_gif` keywords (`delay_cs`/`loop`) into positional args.
- 2026-02-28: Added implementations in `src/runtime/ruby/pytra/py_runtime.rb` for PNG (CRC32/Adler32/zlib store) and GIF (LZW/palette) output, enabling image generation in standalone Ruby.
- 2026-02-28: Added and ran `tools/verify_ruby_sample_artifact_parity.py --samples 01_mandelbrot 06_julia_parameter_sweep`, and confirmed Python vs Ruby byte equality for PNG/GIF.
- 2026-02-28: Ran `runtime_parity_check --case-root sample --targets ruby --all-samples --ignore-unstable-stdout`, and confirmed 18/18 case pass.

## Breakdown

- [x] [ID: P0-RUBY-IMAGE-PARITY-01-S1-01] Inventory current Ruby image-output paths (emitter/runtime) and pin `__pytra_noop` dependency points.
- [x] [ID: P0-RUBY-IMAGE-PARITY-01-S2-01] Implement concrete PNG write logic in Ruby runtime (Python-runtime compatible).
- [x] [ID: P0-RUBY-IMAGE-PARITY-01-S2-02] Implement concrete GIF write logic in Ruby runtime (Python-runtime compatible).
- [x] [ID: P0-RUBY-IMAGE-PARITY-01-S2-03] Switch Ruby emitter image-save lowering from `__pytra_noop` to concrete runtime calls.
- [x] [ID: P0-RUBY-IMAGE-PARITY-01-S3-01] Automate PNG byte-match validation for `sample/01` and integrate it into regression testing.
- [x] [ID: P0-RUBY-IMAGE-PARITY-01-S3-02] Validate byte equality on representative GIF cases and confirm no parity regression after regenerating `sample/ruby`.
