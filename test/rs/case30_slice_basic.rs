// fallback: unsupported annotation: Subscript(value=Name(id='list', ctx=Load()), slice=Name(id='int', ctx=Load()), ctx=Load())
// このファイルは自動生成です。編集しないでください。
// 入力 Python: case30_slice_basic.py

#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;

fn main() {
    let source: &str = r#"# case30: スライス構文 a[b:c] の基本テスト（stepなし）。

def main() -> None:
    nums: list[int] = [10, 20, 30, 40, 50]
    text: str = "abcdef"

    mid_nums: list[int] = nums[1:4]
    mid_text: str = text[2:5]

    print(mid_nums[0])
    print(mid_nums[2])
    print(mid_text)


if __name__ == "__main__":
    main()
"#;
    std::process::exit(py_runtime::run_embedded_python(source));
}
