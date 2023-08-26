#  Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
#  See https://llvm.org/LICENSE.txt for license information.
#  SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception

from setuptools import find_namespace_packages, setup, Distribution


class BinaryDistribution(Distribution):
    """Distribution which always forces a binary package with platform name"""

    def has_ext_modules(foo):
        return True


MLIR_INSTALL_ABS_PATH = Path(__file__).parent.absolute() / "mlir"

# #define LLVM_VERSION_STRING "18.0.0"
llvm_config = open(
    MLIR_INSTALL_ABS_PATH / "include" / "llvm" / "Config" / "llvm-config.h"
).read()
release_version = re.findall(
    r'#define LLVM_VERSION_STRING "(\d+\.\d+\.\d+)"', llvm_config
)
assert release_version, "couldn't find release version in llvm-config.h"
release_version = release_version[0]
commit_hash = os.environ.get("LLVM_PROJECT_COMMIT", "DEADBEEF")

now = datetime.now()
llvm_datetime = os.environ.get(
    "LLVM_DATETIME", f"{now.year}.{now.month}.{now.day}.{now.hour}"
).replace(".", "")

llvm_url = f"https://github.com/llvm/llvm-project/commit/{commit_hash}"
setup(
    name="mlir",
    version=version,
    author="Maksim Levental",
    author_email="maksim.levental@gmail.com",
    description=f"MLIR distribution as wheel. Created at {now} build of {llvm_url}",
    long_description=f"MLIR distribution as wheel. Created at {now} build of [llvm/llvm-project/{commit_hash}]({llvm_url})",
    long_description_content_type="text/markdown",
    include_package_data=True,
    packages=find_namespace_packages(include=["mlir", "mlir.*"]),
    distclass=BinaryDistribution,
    zip_safe=False,
    download_url=llvm_url,
)
