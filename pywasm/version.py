from __future__ import annotations
from pathlib import Path
from datetime import datetime
import os
import re

__all__ = ["dynamic_metadata"]


def __dir__() -> list[str]:
    return __all__


def dynamic_metadata(
    field: str,
    settings: dict[str, object] | None = None,
    _project: dict[str, object] = None,
) -> str:

    if field != "version":
        msg = "Only the 'version' field is supported"
        raise ValueError(msg)

    if settings:
        msg = "No inline configuration is supported"
        raise ValueError(msg)

    now = datetime.now()
    llvm_datetime = os.environ.get(
        "DATETIME", f"{now.year}{now.month:02}{now.day:02}{now.hour:02}"
    )

    cmake_version_path = (
        Path(__file__).parent.parent / "llvm-project/cmake/Modules/LLVMVersion.cmake"
    )
    if not cmake_version_path.exists():
        cmake_version_path = (
            Path(__file__).parent.parent / "llvm-project/llvm/CMakeLists.txt"
        )
    cmake_txt = open(cmake_version_path).read()
    llvm_version = []
    for v in ["LLVM_VERSION_MAJOR", "LLVM_VERSION_MINOR", "LLVM_VERSION_PATCH"]:
        vn = re.findall(rf"set\({v} (\d+)\)", cmake_txt)
        assert vn, f"couldn't find {v} in cmake txt"
        llvm_version.append(vn[0])

    return f"{llvm_version[0]}.{llvm_version[1]}.{llvm_version[2]}.{llvm_datetime}"
