#  Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
#  See https://llvm.org/LICENSE.txt for license information.
#  SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
import os
from datetime import datetime
import re
from pathlib import Path

from setuptools import find_namespace_packages, setup, Distribution

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
now = datetime.now()
llvm_datetime = os.environ.get(
    "LLVM_DATETIME", f"{now.year}.{now.month}.{now.day}.{now.hour}"
)

version = f"{release_version}.{llvm_datetime}+{commit_hash}"

packages = find_namespace_packages(
    include=[
        "mlir",
        "mlir.*",
    ],
)


class BinaryDistribution(Distribution):
    """Distribution which always forces a binary package with platform name"""

    def has_ext_modules(foo):
        return True


setup(
    version=version,
    name="mlir-python-bindings",
    include_package_data=True,
    distclass=BinaryDistribution,
)
