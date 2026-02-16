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

fn pick_25(a: i64, b: i64, flag: bool) -> i64 {
    let mut c: i64 = (if (flag && ((a) > (b))) { a } else { b });
    return c;
}

fn main() {
    py_print(pick_25(10, 3, true));
}
