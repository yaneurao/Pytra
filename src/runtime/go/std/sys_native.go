// sys_native.go: native extern delegates for pytra.std.sys.
package main

import (
	"os"
)

var py_argv []string = append([]string{}, os.Args...)
var py_path []string = []string{}

func py_exit(code int64) {
	os.Exit(int(code))
}

func py_set_argv(values []string) {
	py_argv = append([]string{}, values...)
}

func py_set_path(values []string) {
	py_path = append([]string{}, values...)
}

func py_write_stderr(text string) {
	_, _ = os.Stderr.WriteString(text)
}

func py_write_stdout(text string) {
	_, _ = os.Stdout.WriteString(text)
}
