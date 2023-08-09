#  Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
#  See https://llvm.org/LICENSE.txt for license information.
#  SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
import os
import platform
import re
from datetime import datetime
from pathlib import Path

from setuptools import setup


def get_exe_suffix():
    if platform.system() == "Windows":
        suffix = ".exe"
    else:
        suffix = ""
    return suffix


cmake_txt = open(
    Path(__file__).parent.parent.absolute() / "llvm-project" / "llvm" / "CMakeLists.txt"
).read()
llvm_version = []
for v in ["LLVM_VERSION_MAJOR", "LLVM_VERSION_MINOR", "LLVM_VERSION_PATCH"]:
    vn = re.findall(rf"set\({v} (\d+)\)", cmake_txt)
    assert vn, f"couldn't find {v} in cmake txt"
    llvm_version.append(vn[0])


commit_hash = os.environ.get("LLVM_PROJECT_COMMIT", "DEADBEEF")

now = datetime.now()
llvm_datetime = os.environ.get(
    "LLVM_DATETIME", f"{now.year}.{now.month}.{now.day}.{now.hour}"
)

version = f"{llvm_version[0]}.{llvm_version[1]}.{llvm_version[2]}.{llvm_datetime}+{commit_hash}"

data_files = []
for bin in [
    "llvm-tblgen",
    "mlir-tblgen",
    "mlir-linalg-ods-yaml-gen",
    "mlir-pdll",
    "llvm-config",
    "FileCheck",
]:
    data_files.append(bin + get_exe_suffix())

setup(
    version=version,
    name="mlir-native-tools",
    include_package_data=True,
    data_files=[("bin", data_files)],
)
