// os_native.go: @extern delegation for pytra.std.os.
// Hand-written native implementation.
package main

import "os"

func getcwd() string {
	dir, err := os.Getwd()
	if err != nil {
		panic(err)
	}
	return dir
}
func py_getcwd() string { return getcwd() }

func mkdir(path string, exist_ok bool) {
	if exist_ok {
		if _, err := os.Stat(path); err == nil {
			return
		}
	}
	if err := os.Mkdir(path, 0755); err != nil {
		panic(err)
	}
}
func py_mkdir(path string, exist_ok ...bool) {
	ok := false
	if len(exist_ok) > 0 {
		ok = exist_ok[0]
	}
	mkdir(path, ok)
}

func makedirs(path string, exist_ok bool) {
	_ = exist_ok
	if err := os.MkdirAll(path, 0755); err != nil {
		panic(err)
	}
}
func py_makedirs(path string, exist_ok bool) { makedirs(path, exist_ok) }
