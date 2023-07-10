import datetime
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from pprint import pprint

from setuptools import Extension, setup
from setuptools.command.build_ext import build_ext


class CMakeExtension(Extension):
    def __init__(self, name: str, sourcedir: str = "") -> None:
        super().__init__(name, sources=[])
        self.sourcedir = os.fspath(Path(sourcedir).resolve())


def get_cross_cmake_args():
    cmake_args = {}

    CIBW_ARCHS = os.environ.get("CIBW_ARCHS")
    if CIBW_ARCHS in {"arm64", "aarch64", "ARM64"}:
        ARCH = cmake_args["LLVM_TARGETS_TO_BUILD"] = "AArch64"
    elif CIBW_ARCHS in {"x86_64", "AMD64"}:
        ARCH = cmake_args["LLVM_TARGETS_TO_BUILD"] = "X86"
    else:
        raise ValueError(f"unknown CIBW_ARCHS={CIBW_ARCHS}")
    if CIBW_ARCHS != platform.machine():
        # cmake_args["LLVM_USE_HOST_TOOLS"] = "ON"
        cmake_args["CMAKE_SYSTEM_NAME"] = platform.system()

    if platform.system() == "Darwin":
        if ARCH == "AArch64":
            cmake_args["CMAKE_OSX_ARCHITECTURES"] = "arm64"
            cmake_args["LLVM_DEFAULT_TARGET_TRIPLE"] = "arm64-apple-darwin21.6.0"
            cmake_args["LLVM_HOST_TRIPLE"] = "arm64-apple-darwin21.6.0"
        elif ARCH == "X86":
            cmake_args["CMAKE_OSX_ARCHITECTURES"] = "x86_64"
            cmake_args["LLVM_DEFAULT_TARGET_TRIPLE"] = "x86_64-apple-darwin"
            cmake_args["LLVM_HOST_TRIPLE"] = "x86_64-apple-darwin"
    elif platform.system() == "Linux":
        if ARCH == "AArch64":
            cmake_args["LLVM_DEFAULT_TARGET_TRIPLE"] = "aarch64-linux-gnu"
            cmake_args["LLVM_HOST_TRIPLE"] = "aarch64-linux-gnu"
        elif ARCH == "X86":
            cmake_args["LLVM_DEFAULT_TARGET_TRIPLE"] = "x86_64-unknown-linux-gnu"
            cmake_args["LLVM_HOST_TRIPLE"] = "x86_64-unknown-linux-gnu"

    if BUILD_CUDA:
        cmake_args["LLVM_TARGETS_TO_BUILD"] += ";NVPTX"

    return [f"-D{k}={v}" for k, v in cmake_args.items()]


class CMakeBuild(build_ext):
    def build_extension(self, ext: CMakeExtension) -> None:
        ext_fullpath = Path.cwd() / self.get_ext_fullpath(ext.name)
        extdir = ext_fullpath.parent.resolve()
        cfg = "Release"

        cmake_generator = os.environ.get("CMAKE_GENERATOR", "")

        cmake_args = [
            "-DBUILD_SHARED_LIBS=OFF",
            "-DLLVM_BUILD_BENCHMARKS=OFF",
            "-DLLVM_BUILD_EXAMPLES=OFF",
            "-DLLVM_BUILD_RUNTIMES=OFF",
            "-DLLVM_BUILD_TESTS=OFF",
            "-DLLVM_BUILD_TOOLS=ON",
            "-DLLVM_BUILD_UTILS=ON",
            "-DLLVM_CCACHE_BUILD=ON",
            "-DLLVM_ENABLE_ASSERTIONS=ON",
            "-DLLVM_ENABLE_RTTI=ON",
            "-DLLVM_ENABLE_ZSTD=OFF",
            "-DLLVM_INCLUDE_BENCHMARKS=OFF",
            "-DLLVM_INCLUDE_EXAMPLES=OFF",
            "-DLLVM_INCLUDE_RUNTIMES=OFF",
            "-DLLVM_INCLUDE_TESTS=OFF",
            "-DLLVM_INCLUDE_TOOLS=ON",
            "-DLLVM_INCLUDE_UTILS=ON",
            "-DLLVM_INSTALL_UTILS=ON",
            "-DMLIR_BUILD_MLIR_C_DYLIB=1",
            "-DMLIR_ENABLE_BINDINGS_PYTHON=ON",
            "-DMLIR_ENABLE_EXECUTION_ENGINE=ON",
            "-DMLIR_ENABLE_SPIRV_CPU_RUNNER=ON",
            f"-DCMAKE_INSTALL_PREFIX={extdir}/mlir",
            f"-DCMAKE_LIBRARY_OUTPUT_DIRECTORY={extdir}{os.sep}",
            f"-DPython3_EXECUTABLE={sys.executable}",
            f"-DCMAKE_BUILD_TYPE={cfg}",  # not used on MSVC, but no harm
        ]
        cmake_args += get_cross_cmake_args()
        if os.getenv("LLVM_NATIVE_TOOL_DIR"):
            cmake_args += [
                f"-DLLVM_NATIVE_TOOL_DIR={os.getenv('LLVM_NATIVE_TOOL_DIR')}"
            ]

        LLVM_ENABLE_PROJECTS = "mlir"

        if BUILD_CUDA:
            cmake_args += [
                "-DMLIR_ENABLE_CUDA_RUNNER=ON",
                "-DMLIR_ENABLE_CUDA_CONVERSIONS=ON",
                "-DCMAKE_CUDA_COMPILER=/usr/local/cuda-11.7/bin/nvcc",
            ]

        if BUILD_VULKAN:
            cmake_args += ["-DMLIR_ENABLE_VULKAN_RUNNER=ON"]
            if platform.system() == "Darwin":
                vulkan_library = "/usr/local/lib/libvulkan.dylib"
            elif platform.system() == "Linux":
                vulkan_library = "/usr/local/lib64/libvulkan.so"
            else:
                raise ValueError(f"unknown location for vulkan lib")
            cmake_args += [f"-DVulkan_LIBRARY={vulkan_library}"]

        if BUILD_OPENMP:
            cmake_args += [
                "-DENABLE_CHECK_TARGETS=OFF",
                "-DLIBOMP_OMPD_GDB_SUPPORT=OFF",
                "-DLIBOMP_USE_QUAD_PRECISION=False",
                "-DOPENMP_ENABLE_LIBOMPTARGET=OFF",
            ]
            LLVM_ENABLE_PROJECTS += ";openmp"

        cmake_args += [f"-DLLVM_ENABLE_PROJECTS={LLVM_ENABLE_PROJECTS}"]

        if "CMAKE_ARGS" in os.environ:
            cmake_args += [item for item in os.environ["CMAKE_ARGS"].split(" ") if item]

        build_args = []
        if self.compiler.compiler_type != "msvc":
            # Using Ninja-build since it a) is available as a wheel and b)
            # multithreads automatically. MSVC would require all variables be
            # exported for Ninja to pick it up, which is a little tricky to do.
            # Users can override the generator with CMAKE_GENERATOR in CMake
            # 3.15+.
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
            # Single config generators are handled "normally"
            single_config = any(x in cmake_generator for x in {"NMake", "Ninja"})

            # CMake allows an arch-in-generator style for backward compatibility
            contains_arch = any(x in cmake_generator for x in {"ARM", "Win64"})

            # Specify the arch if using MSVC generator, but only if it doesn't
            # contain a backward-compatibility arch spec already in the
            # generator name.
            if not single_config and not contains_arch:
                PLAT_TO_CMAKE = {
                    "win32": "Win32",
                    "win-amd64": "x64",
                    "win-arm32": "ARM",
                    "win-arm64": "ARM64",
                }
                cmake_args += ["-A", PLAT_TO_CMAKE[self.plat_name]]

            # Multi-config generators have a different way to specify configs
            if not single_config:
                cmake_args += [
                    f"-DCMAKE_LIBRARY_OUTPUT_DIRECTORY_{cfg.upper()}={extdir}"
                ]
                build_args += ["--config", cfg]

        if sys.platform.startswith("darwin"):
            cmake_args += ["-DCMAKE_OSX_DEPLOYMENT_TARGET=11.6"]
            # Cross-compile support for macOS - respect ARCHFLAGS if set
            archs = re.findall(r"-arch (\S+)", os.environ.get("ARCHFLAGS", ""))
            if archs:
                cmake_args += ["-DCMAKE_OSX_ARCHITECTURES={}".format(";".join(archs))]

        if "PARALLEL_LEVEL" not in os.environ:
            build_args += [f"-j{str(2 * os.cpu_count())}"]
        else:
            build_args += [f"-j{os.environ.get('PARALLEL_LEVEL')}"]

        build_temp = Path(self.build_temp) / ext.name
        if not build_temp.exists():
            build_temp.mkdir(parents=True)

        print("ENV", pprint(os.environ))
        print("CMAKE_ARGS", cmake_args)

        subprocess.run(
            ["cmake", ext.sourcedir, *cmake_args], cwd=build_temp, check=True
        )
        subprocess.run(
            ["cmake", "--build", ".", "--target", "install", *build_args],
            cwd=build_temp,
            check=True,
        )
        shutil.move(
            extdir / "mlir" / "python_packages" / "mlir_core" / "mlir",
            extdir / "mlir" / "mlir",
        )


def check_env(build):
    return os.environ.get(build, 0) in {"1", "true", "True", "ON", "YES"}


# LLVM Compiler Infrastructure, release 17.0.0
pstl_release_notes = open("llvm-project/pstl/docs/ReleaseNotes.rst").read()
release_version = re.findall(
    r"LLVM Compiler Infrastructure, release (\d+\.\d+\.\d+)", pstl_release_notes
)
assert release_version, "couldn't find release version in pstl release notes"
release_version = release_version[0]

timestamp = int(time.time())
version = f"{release_version}.{timestamp}"
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
    version += "+" + ".".join(local_version)

commit_hash = os.environ.get("LLVM_PROJECT_COMMIT", "DEADBEEF")
llvm_url = f"https://github.com/llvm/llvm-project/commit/{commit_hash}"
setup(
    name="mlir",
    version=version,
    author="",
    author_email="",
    description=f"MLIR distribution as wheel. Created at {datetime.datetime.now()} build of {llvm_url}",
    long_description=f"MLIR distribution as wheel. Created at {datetime.datetime.now()} build of [llvm/llvm-project/{commit_hash}]({llvm_url})",
    long_description_content_type="text/markdown",
    ext_modules=[CMakeExtension("mlir", sourcedir="llvm-project/llvm")],
    cmdclass={"build_ext": CMakeBuild},
    zip_safe=False,
    python_requires=">=3.11",
    download_url=llvm_url,
)
