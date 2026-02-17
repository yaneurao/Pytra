#include "cpp_module/py_runtime.h"

void __pytra_main() {
    Path root = Path("test/obj/pathlib_case32");
    std::filesystem::create_directories(root);
    Path child = root / "values.txt";
    py_write_text(child, "42");
    py_print(std::filesystem::exists(child));
    py_print(child.filename().string());
    py_print(child.stem().string());
    py_print(std::filesystem::exists(child.parent_path() / "values.txt"));
    py_print(py_read_text(child));
}

int main() {
    __pytra_main();
    return 0;
}
