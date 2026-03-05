"""Target contracts used by ``src/pytra-cli.py``.

This module centralizes per-target output/build/run contracts so the CLI core
does not need to embed target-specific command tables.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


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
}


@dataclass(frozen=True)
class TargetProfile:
    target: str
    extension: str
    build_driver: str
    fixed_output_name: str
    allow_codegen_opt: bool


_TARGET_PROFILES: dict[str, TargetProfile] = {
    "cpp": TargetProfile(target="cpp", extension=".cpp", build_driver="cpp_make", fixed_output_name="", allow_codegen_opt=True),
    "rs": TargetProfile(target="rs", extension=".rs", build_driver="noncpp", fixed_output_name="", allow_codegen_opt=False),
    "cs": TargetProfile(target="cs", extension=".cs", build_driver="noncpp", fixed_output_name="", allow_codegen_opt=False),
    "js": TargetProfile(target="js", extension=".js", build_driver="noncpp", fixed_output_name="", allow_codegen_opt=False),
    "ts": TargetProfile(target="ts", extension=".ts", build_driver="noncpp", fixed_output_name="", allow_codegen_opt=False),
    "go": TargetProfile(target="go", extension=".go", build_driver="noncpp", fixed_output_name="", allow_codegen_opt=False),
    "java": TargetProfile(target="java", extension=".java", build_driver="noncpp", fixed_output_name="Main.java", allow_codegen_opt=False),
    "swift": TargetProfile(target="swift", extension=".swift", build_driver="noncpp", fixed_output_name="", allow_codegen_opt=False),
    "kotlin": TargetProfile(target="kotlin", extension=".kt", build_driver="noncpp", fixed_output_name="", allow_codegen_opt=False),
    "scala": TargetProfile(target="scala", extension=".scala", build_driver="noncpp", fixed_output_name="", allow_codegen_opt=False),
    "lua": TargetProfile(target="lua", extension=".lua", build_driver="noncpp", fixed_output_name="", allow_codegen_opt=False),
    "ruby": TargetProfile(target="ruby", extension=".rb", build_driver="noncpp", fixed_output_name="", allow_codegen_opt=False),
    "php": TargetProfile(target="php", extension=".php", build_driver="noncpp", fixed_output_name="", allow_codegen_opt=False),
    "nim": TargetProfile(target="nim", extension=".nim", build_driver="noncpp", fixed_output_name="", allow_codegen_opt=False),
}


def get_target_profile(target: str) -> TargetProfile:
    profile = _TARGET_PROFILES.get(target)
    if isinstance(profile, TargetProfile):
        return profile
    raise RuntimeError("unsupported target profile: " + target)


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
        exe_path = out_dir / f"{stem}_cs.exe"
        build_cmd = [
            "mcs",
            "-warn:0",
            f"-out:{exe_path}",
            str(output_path),
            str(root / "src/runtime/cs/pytra-core/built_in/py_runtime.cs"),
            str(root / "src/runtime/cs/pytra-core/built_in/time.cs"),
            str(root / "src/runtime/cs/pytra-core/built_in/math.cs"),
            str(root / "src/runtime/cs/pytra-gen/utils/png.cs"),
            str(root / "src/runtime/cs/pytra-gen/utils/gif.cs"),
            str(root / "src/runtime/cs/pytra-core/std/pathlib.cs"),
            str(root / "src/runtime/cs/pytra-core/std/json.cs"),
        ]
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
        run_cmd = (
            [
                "scala",
                "run",
                str(out_dir / "py_runtime.scala"),
                str(out_dir / "image_runtime.scala"),
                str(output_path),
            ]
            if run_after_build
            else None
        )
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

    raise RuntimeError("unsupported non-cpp build target: " + target)
