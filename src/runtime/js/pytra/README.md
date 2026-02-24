# JavaScript runtime（移行中）

- 現在は `src/js_module/` の内容を同名で複製し、`src/runtime/js/pytra/` を新しい参照先として先行導入している。
- 互換期間中は `src/js_module/` を残し、`P1-RUNTIME-05-S3` で旧配置依存を段階撤去する。
- 新規の JS runtime 実装追加先は `src/runtime/js/pytra/` を正本とする。
