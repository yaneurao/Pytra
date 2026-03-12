# TypeScript runtime compatibility lane

- `src/runtime/ts/native/` が手書き runtime の正本です。
- `src/runtime/ts/generated/` が SoT 由来生成 runtime の正本です。
- この `src/runtime/ts/pytra/` には public import path を維持する compat shim だけを置きます。
