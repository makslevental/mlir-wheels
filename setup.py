import os
import platform
import re
import shutil
import subprocess
import sys
from datetime import datetime
from distutils.command.install_data import install_data
from pathlib import Path
from pprint import pprint

from setuptools import Extension, setup
from setuptools.command.build_ext import build_ext


class CMakeExtension(Extension):
    def __init__(self, name: str, sourcedir: str = "") -> None:
        super().__init__(name, sources=[])
        self.sourcedir = os.fspath(Path(sourcedir).resolve())


class MyInstallData(install_data):
    def run(self):
        self.mkpath(self.install_dir)
        for f in self.data_files:
            print(f)

        print(type(self.distribution.data_files))
        for f in self.distribution.data_files:
            print(f)


class CMakeBuild(build_ext):
    def build_extension(self, ext: CMakeExtension) -> None:
        ext_fullpath = Path.cwd() / self.get_ext_fullpath(ext.name)
        extdir = ext_fullpath.parent.resolve()
        install_dir = extdir / "mlir"
        cfg = "Release"

        cmake_generator = os.environ.get("CMAKE_GENERATOR", "Ninja")

        RUN_TESTS = "ON" if check_env("RUN_TESTS") else "OFF"
        # make windows happy
        PYTHON_EXECUTABLE = str(Path(sys.executable))
        if platform.system() == "Windows":
            PYTHON_EXECUTABLE = PYTHON_EXECUTABLE.replace("\\", "\\\\")

        cmake_args = [
            f"-B{build_temp}",
            f"-G {cmake_generator}",
            f"-DCMAKE_BUILD_TYPE={cfg}",  # not used on MSVC, but no harm
            f"-DCMAKE_INSTALL_PREFIX={install_dir}",
            f"-DCMAKE_LIBRARY_OUTPUT_DIRECTORY={extdir}{os.sep}",
            f"-DCMAKE_SYSTEM_NAME={platform.system()}",
            f"-DPython3_EXECUTABLE={PYTHON_EXECUTABLE}",
            # custom
            f"-DBUILD_CUDA={BUILD_CUDA}",
            f"-DBUILD_OPENMP={BUILD_OPENMP}",
            f"-DBUILD_VULKAN={BUILD_VULKAN}",
            f"-DCIBW_ARCHS={os.getenv('CIBW_ARCHS')}",
            f"-DRUN_TESTS={RUN_TESTS}",
        ]

        cmake_args += []

        if "CMAKE_ARGS" in os.environ:
            cmake_args += [item for item in os.environ["CMAKE_ARGS"].split(" ") if item]

        build_args = []
        if self.compiler.compiler_type != "msvc":
            if not cmake_generator or cmake_generator == "Ninja":
                try:
                    import ninja

                    ninja_executable_path = Path(ninja.BIN_DIR) / "ninja"
                    cmake_args += [
                        "-GNinja",
                        f"-DCMAKE_MAKE_PROGRAM:FILEPATH={ninja_executable_path}",
                    ]
                except ImportError:
                    pass

        else:
            single_config = any(x in cmake_generator for x in {"NMake", "Ninja"})
            contains_arch = any(x in cmake_generator for x in {"ARM", "Win64"})
            if not single_config and not contains_arch:
                PLAT_TO_CMAKE = {
                    "win32": "Win32",
                    "win-amd64": "x64",
                    "win-arm32": "ARM",
                    "win-arm64": "ARM64",
                }
                cmake_args += ["-A", PLAT_TO_CMAKE[self.plat_name]]
            if not single_config:
                cmake_args += [
                    f"-DCMAKE_LIBRARY_OUTPUT_DIRECTORY_{cfg.upper()}={extdir}"
                ]
                build_args += ["--config", cfg]

        if sys.platform.startswith("darwin"):
            macosx_deployment_target = os.getenv("MACOSX_DEPLOYMENT_TARGET", "11.6")
            cmake_args += [f"-DCMAKE_OSX_DEPLOYMENT_TARGET={macosx_deployment_target}"]
            # Cross-compile support for macOS - respect ARCHFLAGS if set
            archs = re.findall(r"-arch (\S+)", os.environ.get("ARCHFLAGS", ""))
            if archs:
                cmake_args += ["-DCMAKE_OSX_ARCHITECTURES={}".format(";".join(archs))]

        if "PARALLEL_LEVEL" not in os.environ:
            build_args += [f"-j{str(2 * os.cpu_count())}"]
        else:
            build_args += [f"-j{os.environ.get('PARALLEL_LEVEL')}"]

        config_cmake = Path(__file__).parent.resolve() / "config.cmake"
        assert config_cmake.exists()
        cmake_args.append(f"-C {config_cmake}")

        print("ENV", pprint(os.environ), file=sys.stderr)
        print("CMAKE_ARGS", cmake_args, file=sys.stderr)

        subprocess.run(
            ["cmake", ext.sourcedir, *cmake_args], cwd=build_temp, check=True
        )
        if check_env("DEBUG_CI_FAST_BUILD"):
            subprocess.run(
                ["cmake", "--build", ".", "--target", "llvm-tblgen", *build_args],
                cwd=build_temp,
                check=True,
            )
            shutil.rmtree(install_dir / "bin", ignore_errors=True)
            shutil.copytree(build_temp / "bin", install_dir / "bin")
        else:
            subprocess.run(
                ["cmake", "--build", ".", "--target", "install", *build_args],
                cwd=build_temp,
                check=True,
            )
            if RUN_TESTS:
                env = os.environ.copy()
                # PYTHONPATH needs to be set to find build deps like numpy
                # https://github.com/llvm/llvm-project/pull/89296
                env["MLIR_LIT_PYTHONPATH"] = os.pathsep.join(sys.path)
                subprocess.run(
                    ["cmake", "--build", ".", "--target", "check-all", *build_args],
                    cwd=build_temp,
                    env=env,
                    check=False,
                )
            shutil.rmtree(install_dir / "python_packages", ignore_errors=True)

        subprocess.run(
            [
                "find",
                ".",
                "-exec",
                "touch",
                "-a",
                "-m",
                "-t",
                "197001010000",
                "{}",
                ";",
            ],
            cwd=install_dir,
            check=False,
        )


def check_env(build):
    return os.environ.get(build, 0) in {"1", "true", "True", "ON", "YES"}


cmake_txt = open("llvm-project/cmake/Modules/LLVMVersion.cmake").read()
llvm_version = []
for v in ["LLVM_VERSION_MAJOR", "LLVM_VERSION_MINOR", "LLVM_VERSION_PATCH"]:
    vn = re.findall(rf"set\({v} (\d+)\)", cmake_txt)
    assert vn, f"couldn't find {v} in cmake txt"
    llvm_version.append(vn[0])

commit_hash = os.environ.get("LLVM_PROJECT_COMMIT", "DEADBEEF")

now = datetime.now()
llvm_datetime = os.environ.get(
    "DATETIME", f"{now.year}{now.month:02}{now.day:02}{now.hour:02}"
)

version = f"{llvm_version[0]}.{llvm_version[1]}.{llvm_version[2]}.{llvm_datetime}+"

local_version = []
BUILD_CUDA = check_env("BUILD_CUDA")
if BUILD_CUDA:
    local_version += ["cuda"]
BUILD_VULKAN = check_env("BUILD_VULKAN")
if BUILD_VULKAN:
    local_version += ["vulkan"]
BUILD_OPENMP = check_env("BUILD_OPENMP")
if BUILD_OPENMP:
    local_version += ["openmp"]
if local_version:
    version += ".".join(local_version + [commit_hash])
else:
    version += commit_hash

if len(sys.argv) > 1 and sys.argv[1] == "--mlir-version":
    print(version)
    exit()

llvm_url = f"https://github.com/llvm/llvm-project/commit/{commit_hash}"

build_temp = Path.cwd() / "build" / "temp"
if not build_temp.exists():
    build_temp.mkdir(parents=True)

EXE_EXT = ".exe" if platform.system() == "Windows" else ""
if not check_env("DEBUG_CI_FAST_BUILD") and not BUILD_CUDA:
    exes = [
        "mlir-cpu-runner",
        "mlir-opt",
        "mlir-translate",
    ]
else:
    exes = ["llvm-tblgen"]

data_files = [("bin", [str(build_temp / "bin" / x) + EXE_EXT for x in exes])]

setup(
    name="mlir",
    version=version,
    author="Maksim Levental",
    author_email="maksim.levental@gmail.com",
    description=f"MLIR distribution as wheel. Created at {now} build of {llvm_url}",
    long_description=f"MLIR distribution as wheel. Created at {now} build of [llvm/llvm-project/{commit_hash}]({llvm_url})",
    long_description_content_type="text/markdown",
    ext_modules=[CMakeExtension("mlir", sourcedir="llvm-project/llvm")],
    cmdclass={"build_ext": CMakeBuild},
    zip_safe=False,
    download_url=llvm_url,
    data_files=data_files,
)
