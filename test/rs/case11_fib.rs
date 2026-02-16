// このファイルは自動生成です（native Rust mode）。

trait PyStringify {
    fn py_stringify(&self) -> String;
}
impl PyStringify for bool {
    fn py_stringify(&self) -> String {
        if *self { "True".to_string() } else { "False".to_string() }
    }
}
impl PyStringify for i64 { fn py_stringify(&self) -> String { format!("{}", self) } }
impl PyStringify for i32 { fn py_stringify(&self) -> String { format!("{}", self) } }
impl PyStringify for i16 { fn py_stringify(&self) -> String { format!("{}", self) } }
impl PyStringify for i8 { fn py_stringify(&self) -> String { format!("{}", self) } }
impl PyStringify for u64 { fn py_stringify(&self) -> String { format!("{}", self) } }
impl PyStringify for u32 { fn py_stringify(&self) -> String { format!("{}", self) } }
impl PyStringify for u16 { fn py_stringify(&self) -> String { format!("{}", self) } }
impl PyStringify for u8 { fn py_stringify(&self) -> String { format!("{}", self) } }
impl PyStringify for f64 { fn py_stringify(&self) -> String { format!("{}", self) } }
impl PyStringify for f32 { fn py_stringify(&self) -> String { format!("{}", self) } }
impl PyStringify for String { fn py_stringify(&self) -> String { self.clone() } }
impl PyStringify for &str { fn py_stringify(&self) -> String { (*self).to_string() } }

fn py_print<T: PyStringify>(v: T) {
    println!("{}", v.py_stringify());
}

fn fib(n: i64) -> i64 {
    if ((n) <= (1)) {
        return n;
    }
    return ((fib(((n) - (1)))) + (fib(((n) - (2)))));
}

fn main() {
    py_print(fib(10));
}
