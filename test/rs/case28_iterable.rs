// fallback: unsupported annotation: Subscript(value=Name(id='list', ctx=Load()), slice=Name(id='int', ctx=Load()), ctx=Load())
// このファイルは自動生成です。編集しないでください。
// 入力 Python: case28_iterable.py

#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;

fn main() {
    let source: &str = r#"
def main():

    l : list[int] = [1, 2, 3]
    sum = 0
    for v in l:
        sum += v
    print(sum)

if __name__ == "__main__":
    main()
"#;
    std::process::exit(py_runtime::run_embedded_python(source));
}
