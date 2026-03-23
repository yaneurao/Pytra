"""Target contracts used by ``src/pytra-cli.py``.

This module centralizes per-target output/build/run contracts so the CLI core
does not need to embed target-specific command tables.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from toolchain.misc.backend_registry_diagnostics import unsupported_noncpp_build_target_message
from toolchain.misc.backend_registry_diagnostics import unsupported_target_profile_message


SUPPORTED_TARGETS: list[str] = [
    "cpp",
    "rs",
    "cs",
    "js",
    "ts",
    "go",
    "java",
    "swift",
    "kotlin",
    "scala",
    "lua",
    "ruby",
    "php",
    "nim",
    "dart",
]

TARGET_EXT: dict[str, str] = {
    "cpp": ".cpp",
    "rs": ".rs",
    "cs": ".cs",
    "js": ".js",
    "ts": ".ts",
    "go": ".go",
    "java": ".java",
    "swift": ".swift",
    "kotlin": ".kt",
    "scala": ".scala",
    "lua": ".lua",
    "ruby": ".rb",
    "php": ".php",
    "nim": ".nim",
    "dart": ".dart",
}


@dataclass(frozen=True)
class TargetProfile:
    target: str
    extension: str
    build_driver: str
    fixed_output_name: str
    allow_codegen_opt: bool
    runner_needs: tuple[str, ...]


_TARGET_PROFILES: dict[str, TargetProfile] = {
    "cpp": TargetProfile(target="cpp", extension=".cpp", build_driver="cpp_make", fixed_output_name="", allow_codegen_opt=True, runner_needs=("python", "make", "g++")),
    "rs": TargetProfile(target="rs", extension=".rs", build_driver="noncpp", fixed_output_name="", allow_codegen_opt=False, runner_needs=("python", "rustc")),
    "cs": TargetProfile(target="cs", extension=".cs", build_driver="noncpp", fixed_output_name="", allow_codegen_opt=False, runner_needs=("python", "mcs")),
    "js": TargetProfile(target="js", extension=".js", build_driver="noncpp", fixed_output_name="", allow_codegen_opt=False, runner_needs=("python", "node")),
    "ts": TargetProfile(target="ts", extension=".ts", build_driver="noncpp", fixed_output_name="", allow_codegen_opt=False, runner_needs=("python", "node", "npx")),
    "go": TargetProfile(target="go", extension=".go", build_driver="noncpp", fixed_output_name="", allow_codegen_opt=False, runner_needs=("python", "go")),
    "java": TargetProfile(target="java", extension=".java", build_driver="noncpp", fixed_output_name="Main.java", allow_codegen_opt=False, runner_needs=("python", "javac", "java")),
    "swift": TargetProfile(target="swift", extension=".swift", build_driver="noncpp", fixed_output_name="", allow_codegen_opt=False, runner_needs=("python", "swiftc")),
    "kotlin": TargetProfile(target="kotlin", extension=".kt", build_driver="noncpp", fixed_output_name="", allow_codegen_opt=False, runner_needs=("python", "kotlinc", "java")),
    "scala": TargetProfile(target="scala", extension=".scala", build_driver="noncpp", fixed_output_name="", allow_codegen_opt=False, runner_needs=("python", "scala-cli")),
    "lua": TargetProfile(target="lua", extension=".lua", build_driver="noncpp", fixed_output_name="", allow_codegen_opt=False, runner_needs=("python", "lua")),
    "ruby": TargetProfile(target="ruby", extension=".rb", build_driver="noncpp", fixed_output_name="", allow_codegen_opt=False, runner_needs=("python", "ruby")),
    "php": TargetProfile(target="php", extension=".php", build_driver="noncpp", fixed_output_name="", allow_codegen_opt=False, runner_needs=("python", "php")),
    "nim": TargetProfile(target="nim", extension=".nim", build_driver="noncpp", fixed_output_name="main.nim", allow_codegen_opt=False, runner_needs=("python", "nim")),
    "dart": TargetProfile(target="dart", extension=".dart", build_driver="noncpp", fixed_output_name="", allow_codegen_opt=False, runner_needs=("python", "dart")),
}


def get_target_profile(target: str) -> TargetProfile:
    profile = _TARGET_PROFILES.get(target)
    if isinstance(profile, TargetProfile):
        return profile
    raise RuntimeError(unsupported_target_profile_message(target))


def list_supported_targets() -> list[str]:
    return list(SUPPORTED_TARGETS)


def list_parity_targets() -> list[str]:
    # Keep parity output order stable for existing logs and README refresh tooling.
    return ["cpp", "rs", "cs", "js", "ruby", "lua", "php", "ts", "go", "java", "swift", "kotlin", "scala", "nim", "dart"]


def validate_profile_option_compatibility(
    profile: TargetProfile,
    *,
    codegen_opt: int | None,
    build: bool,
    compiler: str,
    std: str,
    opt: str,
    exe: str,
) -> str:
    if codegen_opt is not None and not profile.allow_codegen_opt:
        return "--codegen-opt is supported only for target cpp"
    if profile.build_driver == "noncpp" and build:
        if compiler != "g++" or std != "c++20" or opt != "-O2" or exe != "app.out":
            return "--compiler/--std/--opt/--exe are supported only for target cpp --build"
    return ""


@dataclass(frozen=True)
class NonCppBuildPlan:
    build_cmd: list[str] | None
    run_cmd: list[str] | None


def resolve_output_path(input_path: Path, target: str, output: str, output_dir: str) -> Path:
    if output != "":
        return Path(output)
    profile = get_target_profile(target)
    out_dir = Path(output_dir) if output_dir != "" else Path("out")
    if profile.fixed_output_name != "":
        return out_dir / profile.fixed_output_name
    stem = input_path.stem if input_path.stem != "" else "output"
    ext = profile.extension
    if ext == "":
        return out_dir / stem
    return out_dir / f"{stem}{ext}"


def make_noncpp_build_plan(
    *,
    root: Path,
    target: str,
    output_path: Path,
    source_stem: str,
    run_after_build: bool,
) -> NonCppBuildPlan:
    out_dir = output_path.parent
    stem = source_stem if source_stem != "" else "output"

    if target == "js":
        run_cmd = ["node", str(output_path)] if run_after_build else None
        return NonCppBuildPlan(build_cmd=None, run_cmd=run_cmd)
    if target == "ts":
        run_cmd = ["npx", "-y", "tsx", str(output_path)] if run_after_build else None
        return NonCppBuildPlan(build_cmd=None, run_cmd=run_cmd)
    if target == "ruby":
        run_cmd = ["ruby", str(output_path)] if run_after_build else None
        return NonCppBuildPlan(build_cmd=None, run_cmd=run_cmd)
    if target == "lua":
        run_cmd = ["lua", str(output_path)] if run_after_build else None
        return NonCppBuildPlan(build_cmd=None, run_cmd=run_cmd)
    if target == "php":
        run_cmd = ["php", str(output_path)] if run_after_build else None
        return NonCppBuildPlan(build_cmd=None, run_cmd=run_cmd)

    if target == "rs":
        exe_path = out_dir / f"{stem}_rs.out"
        build_cmd = ["rustc", "-O", str(output_path), "-o", str(exe_path)]
        run_cmd = [str(exe_path)] if run_after_build else None
        return NonCppBuildPlan(build_cmd=build_cmd, run_cmd=run_cmd)

    if target == "cs":
        emit_dir = out_dir / "emit" if (out_dir / "emit").is_dir() else out_dir
        exe_path = out_dir / f"{stem}_cs.exe"
        # Collect all .cs files from emit directory.
        # Override utils/*.cs with generated runtime versions (post-processed helper classes).
        gen_dir = root / "src" / "runtime" / "cs" / "generated"
        cs_files: list[str] = []
        skip_dirs = {"utils"}  # utils are replaced by generated runtime
        for cs_file in sorted(emit_dir.rglob("*.cs")):
            rel_parts = cs_file.relative_to(emit_dir).parts
            if len(rel_parts) > 0 and rel_parts[0] in skip_dirs:
                continue
            cs_files.append(str(cs_file))
        # Add generated utils (png_helper, gif_helper, etc.)
        if gen_dir.is_dir():
            for cs_file in sorted(gen_dir.rglob("*.cs")):
                rel = cs_file.relative_to(gen_dir)
                # Only add utils/ (built_in/ generated files may conflict with py_runtime)
                if str(rel).startswith("utils/") and cs_file.name != "assertions.cs":
                    cs_files.append(str(cs_file))
        build_cmd = ["mcs", "-warn:0", f"-out:{exe_path}"] + cs_files
        run_cmd = ["mono", str(exe_path)] if run_after_build else None
        return NonCppBuildPlan(build_cmd=build_cmd, run_cmd=run_cmd)

    if target == "go":
        exe_path = out_dir / f"{stem}_go.out"
        build_cmd = [
            "go",
            "build",
            "-o",
            str(exe_path),
            str(output_path),
            str(out_dir / "py_runtime.go"),
            str(out_dir / "png.go"),
            str(out_dir / "gif.go"),
        ]
        run_cmd = [str(exe_path)] if run_after_build else None
        return NonCppBuildPlan(build_cmd=build_cmd, run_cmd=run_cmd)

    if target == "java":
        build_cmd = [
            "javac",
            "-sourcepath",
            str(out_dir),
            str(out_dir / "Main.java"),
            str(out_dir / "PyRuntime.java"),
            str(out_dir / "png.java"),
            str(out_dir / "gif.java"),
        ]
        run_cmd = ["java", "-cp", str(out_dir), "Main"] if run_after_build else None
        return NonCppBuildPlan(build_cmd=build_cmd, run_cmd=run_cmd)

    if target == "swift":
        exe_path = out_dir / f"{stem}_swift.out"
        build_cmd = [
            "swiftc",
            "-O",
            str(output_path),
            str(out_dir / "py_runtime.swift"),
            str(out_dir / "image_runtime.swift"),
            "-o",
            str(exe_path),
        ]
        run_cmd = [str(exe_path)] if run_after_build else None
        return NonCppBuildPlan(build_cmd=build_cmd, run_cmd=run_cmd)

    if target == "kotlin":
        jar_path = out_dir / f"{stem}_kotlin.jar"
        build_cmd = [
            "kotlinc",
            str(output_path),
            str(out_dir / "py_runtime.kt"),
            str(out_dir / "image_runtime.kt"),
            "-include-runtime",
            "-d",
            str(jar_path),
        ]
        run_cmd = ["java", "-jar", str(jar_path)] if run_after_build else None
        return NonCppBuildPlan(build_cmd=build_cmd, run_cmd=run_cmd)

    if target == "scala":
        if run_after_build:
            # Scala merges all modules into a single file.
            # Run: merged entry + built_in/py_runtime + std/*_native files.
            scala_files: list[str] = [str(output_path)]
            rt_file = out_dir / "built_in" / "py_runtime.scala"
            if rt_file.exists():
                scala_files.append(str(rt_file))
            import glob as _glob
            for native_f in sorted(_glob.glob(str(out_dir / "std" / "*_native.scala"))):
                scala_files.append(native_f)
            run_cmd = ["scala-cli", "run", "--jvm", "17"] + scala_files
        else:
            run_cmd = None
        return NonCppBuildPlan(build_cmd=None, run_cmd=run_cmd)

    if target == "nim":
        exe_path = out_dir / f"{stem}_nim.out"
        nimcache_path = out_dir / f"nimcache_{stem}"
        build_cmd = [
            "nim",
            "c",
            "--hints:off",
            "--verbosity:0",
            f"--nimcache:{nimcache_path}",
            f"-o:{exe_path}",
        ]
        if run_after_build:
            build_cmd.append("-r")
        build_cmd.append(str(output_path))
        return NonCppBuildPlan(build_cmd=build_cmd, run_cmd=None)

    raise RuntimeError(unsupported_noncpp_build_target_message(target))
