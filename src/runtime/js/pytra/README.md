# JavaScript runtime compatibility lane

- `src/runtime/js/native/` が手書き runtime の正本です。
- `src/runtime/js/generated/` が SoT 由来生成 runtime の正本です。
- この `src/runtime/js/pytra/` には public import path を維持する compat shim だけを置きます。
