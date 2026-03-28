// glob_native.go: @extern delegation for pytra.std.glob.
// Hand-written native implementation.
package main

import "path/filepath"

func glob(pattern string) []string {
	items, err := filepath.Glob(pattern)
	if err != nil {
		panic(err)
	}
	return items
}
func py_glob(pattern string) *PyList[string] { return PyListFromSlice[string](glob(pattern)) }
