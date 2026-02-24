// 互換レイヤ（段階移行中）
// 実体は src/runtime/rs/pytra/built_in/py_runtime.rs に移動済み。
// 既存の #[path = "../../src/rs_module/py_runtime.rs"] 参照を壊さないため、
// ここでは新配置を include! して暫定互換を提供する。
include!("../runtime/rs/pytra/built_in/py_runtime.rs");
