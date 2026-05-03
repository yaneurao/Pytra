from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from toolchain.emit.powershell.cli import _copy_powershell_runtime


class PowerShellCliRuntimeCopyTests(unittest.TestCase):
    def test_copy_powershell_runtime_includes_std_native_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)

            _copy_powershell_runtime(out_dir)

            self.assertTrue((out_dir / "built_in" / "py_runtime.ps1").exists())
            self.assertTrue((out_dir / "std" / "json_native.ps1").exists())
            self.assertTrue((out_dir / "std" / "pathlib_native.ps1").exists())


if __name__ == "__main__":
    unittest.main()
