# Rust Runtime Layout

このディレクトリは Rust runtime の正本配置です。

- `built_in/`: Python 組み込み互換の基盤実装
- `std/`: `pytra.std.*` 相当
- `utils/`: `pytra.utils.*` 相当
- `compiler/`: compiler 補助（必要時）

`src/rs_module/` は移行期間の互換レイヤです。
