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
const pytraEmbeddedSourceBase64 = "IyAxMjog44OQ44OW44Or44K944O844OI44Gu6YCU5Lit54q25oWL44KSR0lG5Ye65Yqb44GZ44KL44K144Oz44OX44Or44CCCgpmcm9tIF9fZnV0dXJlX18gaW1wb3J0IGFubm90YXRpb25zCgpmcm9tIHRpbWUgaW1wb3J0IHBlcmZfY291bnRlcgoKZnJvbSBweV9tb2R1bGUuZ2lmX2hlbHBlciBpbXBvcnQgZ3JheXNjYWxlX3BhbGV0dGUsIHNhdmVfZ2lmCgoKZGVmIHJlbmRlcih2YWx1ZXM6IGxpc3RbaW50XSwgdzogaW50LCBoOiBpbnQpIC0+IGJ5dGVzOgogICAgZnJhbWUgPSBieXRlYXJyYXkodyAqIGgpCiAgICBuID0gbGVuKHZhbHVlcykKICAgIGJhcl93ID0gdyAvIG4KICAgIGZvciBpIGluIHJhbmdlKG4pOgogICAgICAgIHgwID0gaW50KGkgKiBiYXJfdykKICAgICAgICB4MSA9IGludCgoaSArIDEpICogYmFyX3cpCiAgICAgICAgaWYgeDEgPD0geDA6CiAgICAgICAgICAgIHgxID0geDAgKyAxCiAgICAgICAgYmggPSBpbnQoKCh2YWx1ZXNbaV0gLyBuKSAqIGgpKQogICAgICAgIHkgPSBoIC0gYmgKICAgICAgICBmb3IgeSBpbiByYW5nZSh5LCBoKToKICAgICAgICAgICAgZm9yIHggaW4gcmFuZ2UoeDAsIHgxKToKICAgICAgICAgICAgICAgIGZyYW1lW3kgKiB3ICsgeF0gPSAyNTUKICAgIHJldHVybiBieXRlcyhmcmFtZSkKCgpkZWYgcnVuXzEyX3NvcnRfdmlzdWFsaXplcigpIC0+IE5vbmU6CiAgICB3ID0gMzIwCiAgICBoID0gMTgwCiAgICBuID0gMTI0CiAgICBvdXRfcGF0aCA9ICJzYW1wbGUvb3V0LzEyX3NvcnRfdmlzdWFsaXplci5naWYiCgogICAgc3RhcnQgPSBwZXJmX2NvdW50ZXIoKQogICAgdmFsdWVzOiBsaXN0W2ludF0gPSBbXQogICAgZm9yIGkgaW4gcmFuZ2Uobik6CiAgICAgICAgdmFsdWVzLmFwcGVuZCgoaSAqIDM3ICsgMTkpICUgbikKCiAgICBmcmFtZXM6IGxpc3RbYnl0ZXNdID0gW3JlbmRlcih2YWx1ZXMsIHcsIGgpXQoKICAgIG9wID0gMAogICAgZm9yIGkgaW4gcmFuZ2Uobik6CiAgICAgICAgc3dhcHBlZCA9IEZhbHNlCiAgICAgICAgZm9yIGogaW4gcmFuZ2UobiAtIGkgLSAxKToKICAgICAgICAgICAgaWYgdmFsdWVzW2pdID4gdmFsdWVzW2ogKyAxXToKICAgICAgICAgICAgICAgIHRtcCA9IHZhbHVlc1tqXQogICAgICAgICAgICAgICAgdmFsdWVzW2pdID0gdmFsdWVzW2ogKyAxXQogICAgICAgICAgICAgICAgdmFsdWVzW2ogKyAxXSA9IHRtcAogICAgICAgICAgICAgICAgc3dhcHBlZCA9IFRydWUKICAgICAgICAgICAgaWYgb3AgJSA4ID09IDA6CiAgICAgICAgICAgICAgICBmcmFtZXMuYXBwZW5kKHJlbmRlcih2YWx1ZXMsIHcsIGgpKQogICAgICAgICAgICBvcCArPSAxCiAgICAgICAgaWYgbm90IHN3YXBwZWQ6CiAgICAgICAgICAgIGJyZWFrCgogICAgc2F2ZV9naWYob3V0X3BhdGgsIHcsIGgsIGZyYW1lcywgZ3JheXNjYWxlX3BhbGV0dGUoKSwgZGVsYXlfY3M9MywgbG9vcD0wKQogICAgZWxhcHNlZCA9IHBlcmZfY291bnRlcigpIC0gc3RhcnQKICAgIHByaW50KCJvdXRwdXQ6Iiwgb3V0X3BhdGgpCiAgICBwcmludCgiZnJhbWVzOiIsIGxlbihmcmFtZXMpKQogICAgcHJpbnQoImVsYXBzZWRfc2VjOiIsIGVsYXBzZWQpCgoKaWYgX19uYW1lX18gPT0gIl9fbWFpbl9fIjoKICAgIHJ1bl8xMl9zb3J0X3Zpc3VhbGl6ZXIoKQo="

// main は埋め込み Python を実行するエントリポイント。
func main() {
	os.Exit(pytraRunEmbeddedPython(pytraEmbeddedSourceBase64, os.Args[1:]))
}
