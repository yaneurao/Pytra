"""Emit stage entry points: linked EAST → target language source.

Each submodule is a standalone entry point for a specific target language:
  - toolchain.emit.cpp  — C++ (import-isolated, multi-file)
  - toolchain.emit.rs   — Rust
  - toolchain.emit.all  — all backends (generic)
  - ...
"""
