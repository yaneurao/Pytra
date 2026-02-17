#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{math_tan, math_exp, math_log, math_log10, math_fabs, math_ceil, math_pow, py_print};

// このファイルは自動生成です（native Rust mode）。

fn main() -> () {
    py_print(((math_fabs(((math_tan(((0.0) as f64))) as f64))) < (1e-12)));
    py_print(((math_fabs(((((math_log(((math_exp(((1.0) as f64))) as f64))) - (1.0))) as f64))) < (1e-12)));
    py_print(((math_log10(((1000.0) as f64))) as i64));
    py_print(((((math_fabs((((-3.5)) as f64))) * (10.0))) as i64));
    py_print(((math_ceil(((2.1) as f64))) as i64));
    py_print(((math_pow(((2.0) as f64), ((5.0) as f64))) as i64));
}
