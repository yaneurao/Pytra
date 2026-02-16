// このファイルは自動生成です。編集しないでください。
// 入力 Python: case30_slice_basic.py

use std::env;
use std::process::Command;

fn run_with(interpreter: &str, source: &str) -> Option<i32> {
    let mut cmd = Command::new(interpreter);
    cmd.arg("-c").arg(source);

    // sample/py が `from py_module ...` を使うため `PYTHONPATH=src` を付与する。
    let py_path = match env::var("PYTHONPATH") {
        Ok(v) if !v.is_empty() => format!("src:{}", v),
        _ => "src".to_string(),
    };
    cmd.env("PYTHONPATH", py_path);

    // 親プロセスの標準入出力をそのまま使う。
    let status = cmd.status().ok()?;
    Some(status.code().unwrap_or(1))
}

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

    // python3 を優先し、無ければ python を試す。
    if let Some(code) = run_with("python3", source) {
        std::process::exit(code);
    }
    if let Some(code) = run_with("python", source) {
        std::process::exit(code);
    }

    eprintln!("error: python interpreter not found (python3/python)");
    std::process::exit(1);
}
