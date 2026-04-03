import Foundation

func exit(_ code: Int64 = Int64(0)) {
    sys_native_exit(code)
}

func set_argv(_ values: [Any]) {
    sys_native_set_argv(values)
}

func set_path(_ values: [Any]) {
    sys_native_set_path(values)
}

func write_stderr(_ text: String) {
    sys_native_write_stderr(text)
}

func write_stdout(_ text: String) {
    sys_native_write_stdout(text)
}

var argv: [Any] = __pytra_sys_argv
var path: [Any] = __pytra_sys_path
var stderr: String = sys_native_stderr()
var stdout: String = sys_native_stdout()
