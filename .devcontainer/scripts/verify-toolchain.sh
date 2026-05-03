#!/usr/bin/env bash
set -euo pipefail

run() {
  printf '\n==> %s\n' "$*"
  "$@"
}

run python3 --version
run pip --version
run pytest --version
run gcc --version
run g++ --version
run clang --version
run cmake --version
run ninja --version
run java -version
run javac -version
run mono --version
run mcs --version
run php --version
run lua -v
run luarocks --version
run node --version
run npm --version
run tsc --version
run go version
run rustc --version
run cargo --version
run dart --version
run zig version
run dotnet --info
run pwsh -NoLogo -NoProfile -Command '$PSVersionTable.PSVersion.ToString()'
run ruby --version

if command -v swift >/dev/null 2>&1; then
  run swift --version
else
  printf '\n==> swift optional: not installed in the Linux devcontainer\n'
fi
