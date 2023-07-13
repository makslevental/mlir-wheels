#  Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
#  See https://llvm.org/LICENSE.txt for license information.
#  SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
import os
import platform
import re
from pathlib import Path

from setuptools import setup


def get_exe_suffix():
    if platform.system() == "Windows":
        suffix = ".exe"
    else:
        suffix = ""
    return suffix


# LLVM Compiler Infrastructure, release 17.0.0
pstl_release_notes = open(
    Path(__file__).parent.parent.absolute()
    / "llvm-project"
    / "pstl"
    / "docs"
    / "ReleaseNotes.rst"
).read()
release_version = re.findall(
    r"LLVM Compiler Infrastructure, release (\d+\.\d+\.\d+)", pstl_release_notes
)
assert release_version, "couldn't find release version in pstl release notes"
release_version = release_version[0]
commit_hash = os.environ.get("LLVM_PROJECT_COMMIT", "DEADBEEF")

version = f"{release_version}+{commit_hash}"

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
    name="native_tools",
    include_package_data=True,
    data_files=[("bin", data_files)],
)
