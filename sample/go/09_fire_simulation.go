// このファイルは自動生成です（Python -> Go embedded mode）。

// Python 埋め込み実行向けの Go ランタイム補助。
// 生成された Go コードから呼び出し、Python ソースを一時ファイルに展開して実行する。

package main

import (
	"encoding/base64"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
)

// pytraRunEmbeddedPython は、Base64 で埋め込まれた Python ソースを実行する。
//
// Args:
//   sourceBase64: 埋め込み Python ソースコード（Base64 文字列）。
//   args: Python スクリプトへ渡す引数。
//
// Returns:
//   Python プロセスの終了コード。異常時は 1 を返す。
func pytraRunEmbeddedPython(sourceBase64 string, args []string) int {
	sourceBytes, decodeErr := base64.StdEncoding.DecodeString(sourceBase64)
	if decodeErr != nil {
		fmt.Fprintln(os.Stderr, "error: failed to decode embedded python source")
		return 1
	}

	tempDir, mkErr := os.MkdirTemp("", "pytra_go_")
	if mkErr != nil {
		fmt.Fprintln(os.Stderr, "error: failed to create temp directory")
		return 1
	}
	defer os.RemoveAll(tempDir)

	scriptPath := filepath.Join(tempDir, "embedded.py")
	if writeErr := os.WriteFile(scriptPath, sourceBytes, 0o600); writeErr != nil {
		fmt.Fprintln(os.Stderr, "error: failed to write temp python script")
		return 1
	}

	pythonPath := "src"
	if current, ok := os.LookupEnv("PYTHONPATH"); ok && current != "" {
		pythonPath = pythonPath + string(os.PathListSeparator) + current
	}

	run := func(interpreter string) (int, error) {
		cmd := exec.Command(interpreter, append([]string{scriptPath}, args...)...)
		cmd.Stdout = os.Stdout
		cmd.Stderr = os.Stderr
		cmd.Stdin = os.Stdin
		env := os.Environ()
		env = append(env, "PYTHONPATH="+pythonPath)
		cmd.Env = env
		err := cmd.Run()
		if err == nil {
			return 0, nil
		}
		if exitErr, ok := err.(*exec.ExitError); ok {
			return exitErr.ExitCode(), nil
		}
		return 0, err
	}

	if code, err := run("python3"); err == nil {
		return code
	}
	if code, err := run("python"); err == nil {
		return code
	}

	fmt.Fprintln(os.Stderr, "error: python interpreter not found (python3/python)")
	return 1
}

// 埋め込み Python ソース（Base64）。
const pytraEmbeddedSourceBase64 = "IyAwOTog57Ch5piT44OV44Kh44Kk44Ki44Ko44OV44Kn44Kv44OI44KSR0lG5Ye65Yqb44GZ44KL44K144Oz44OX44Or44CCCgpmcm9tIF9fZnV0dXJlX18gaW1wb3J0IGFubm90YXRpb25zCgpmcm9tIHRpbWUgaW1wb3J0IHBlcmZfY291bnRlcgoKZnJvbSBweV9tb2R1bGUuZ2lmX2hlbHBlciBpbXBvcnQgc2F2ZV9naWYKCgpkZWYgZmlyZV9wYWxldHRlKCkgLT4gYnl0ZXM6CiAgICBwID0gYnl0ZWFycmF5KCkKICAgIGZvciBpIGluIHJhbmdlKDI1Nik6CiAgICAgICAgciA9IDAKICAgICAgICBnID0gMAogICAgICAgIGIgPSAwCiAgICAgICAgaWYgaSA8IDg1OgogICAgICAgICAgICByID0gaSAqIDMKICAgICAgICAgICAgZyA9IDAKICAgICAgICAgICAgYiA9IDAKICAgICAgICBlbGlmIGkgPCAxNzA6CiAgICAgICAgICAgIHIgPSAyNTUKICAgICAgICAgICAgZyA9IChpIC0gODUpICogMwogICAgICAgICAgICBiID0gMAogICAgICAgIGVsc2U6CiAgICAgICAgICAgIHIgPSAyNTUKICAgICAgICAgICAgZyA9IDI1NQogICAgICAgICAgICBiID0gKGkgLSAxNzApICogMwogICAgICAgIHAuYXBwZW5kKHIpCiAgICAgICAgcC5hcHBlbmQoZykKICAgICAgICBwLmFwcGVuZChiKQogICAgcmV0dXJuIGJ5dGVzKHApCgoKZGVmIHJ1bl8wOV9maXJlX3NpbXVsYXRpb24oKSAtPiBOb25lOgogICAgdyA9IDM4MAogICAgaCA9IDI2MAogICAgc3RlcHMgPSA0MjAKICAgIG91dF9wYXRoID0gInNhbXBsZS9vdXQvMDlfZmlyZV9zaW11bGF0aW9uLmdpZiIKCiAgICBzdGFydCA9IHBlcmZfY291bnRlcigpCiAgICBoZWF0OiBsaXN0W2xpc3RbaW50XV0gPSBbXQogICAgZm9yIF8gaW4gcmFuZ2UoaCk6CiAgICAgICAgcm93OiBsaXN0W2ludF0gPSBbXQogICAgICAgIGZvciBfIGluIHJhbmdlKHcpOgogICAgICAgICAgICByb3cuYXBwZW5kKDApCiAgICAgICAgaGVhdC5hcHBlbmQocm93KQogICAgZnJhbWVzOiBsaXN0W2J5dGVzXSA9IFtdCgogICAgZm9yIHQgaW4gcmFuZ2Uoc3RlcHMpOgogICAgICAgIGZvciB4IGluIHJhbmdlKHcpOgogICAgICAgICAgICB2YWwgPSAxNzAgKyAoKHggKiAxMyArIHQgKiAxNykgJSA4NikKICAgICAgICAgICAgaGVhdFtoIC0gMV1beF0gPSB2YWwKCiAgICAgICAgZm9yIHkgaW4gcmFuZ2UoMSwgaCk6CiAgICAgICAgICAgIGZvciB4IGluIHJhbmdlKHcpOgogICAgICAgICAgICAgICAgYSA9IGhlYXRbeV1beF0KICAgICAgICAgICAgICAgIGIgPSBoZWF0W3ldWyh4IC0gMSArIHcpICUgd10KICAgICAgICAgICAgICAgIGMgPSBoZWF0W3ldWyh4ICsgMSkgJSB3XQogICAgICAgICAgICAgICAgZCA9IGhlYXRbKHkgKyAxKSAlIGhdW3hdCiAgICAgICAgICAgICAgICB2ID0gKGEgKyBiICsgYyArIGQpIC8vIDQKICAgICAgICAgICAgICAgIGNvb2wgPSAxICsgKCh4ICsgeSArIHQpICUgMykKICAgICAgICAgICAgICAgIG52ID0gdiAtIGNvb2wKICAgICAgICAgICAgICAgIGhlYXRbeSAtIDFdW3hdID0gbnYgaWYgbnYgPiAwIGVsc2UgMAoKICAgICAgICBmcmFtZSA9IGJ5dGVhcnJheSh3ICogaCkKICAgICAgICBpID0gMAogICAgICAgIGZvciB5eSBpbiByYW5nZShoKToKICAgICAgICAgICAgZm9yIHh4IGluIHJhbmdlKHcpOgogICAgICAgICAgICAgICAgZnJhbWVbaV0gPSBoZWF0W3l5XVt4eF0KICAgICAgICAgICAgICAgIGkgKz0gMQogICAgICAgIGZyYW1lcy5hcHBlbmQoYnl0ZXMoZnJhbWUpKQoKICAgIHNhdmVfZ2lmKG91dF9wYXRoLCB3LCBoLCBmcmFtZXMsIGZpcmVfcGFsZXR0ZSgpLCBkZWxheV9jcz00LCBsb29wPTApCiAgICBlbGFwc2VkID0gcGVyZl9jb3VudGVyKCkgLSBzdGFydAogICAgcHJpbnQoIm91dHB1dDoiLCBvdXRfcGF0aCkKICAgIHByaW50KCJmcmFtZXM6Iiwgc3RlcHMpCiAgICBwcmludCgiZWxhcHNlZF9zZWM6IiwgZWxhcHNlZCkKCgppZiBfX25hbWVfXyA9PSAiX19tYWluX18iOgogICAgcnVuXzA5X2ZpcmVfc2ltdWxhdGlvbigpCg=="

// main は埋め込み Python を実行するエントリポイント。
func main() {
	os.Exit(pytraRunEmbeddedPython(pytraEmbeddedSourceBase64, os.Args[1:]))
}
