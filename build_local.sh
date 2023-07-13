#!/usr/bin/env bash
set -xe

unameOut="$(uname -s)"
case "${unameOut}" in
    Linux*)     machine=Linux;;
    Darwin*)    machine=Mac;;
    CYGWIN*)    machine=Cygwin;;
    MINGW*)     machine=MinGw;;
    MSYS_NT*)   machine=Git;;
    *)          machine="UNKNOWN:${unameOut}"
esac
echo ${machine}

export HOST_CCACHE_DIR="$(ccache --get-config cache_dir)"
export PARALLEL_LEVEL=15
export BUILD_CUDA=false
export BUILD_OPENMP=true
export BUILD_VULKAN=false

if [ "$machine" == "Linux" ]; then
  export LLVM_PROJECT_MAIN_SRC_DIR=/project/llvm-project
else
  export LLVM_PROJECT_MAIN_SRC_DIR=llvm-project
fi

export MATRIX_OS=ubuntu-20.04
export CIBW_ARCHS=x86_64
export ARCH=x86_64
cibuildwheel --platform linux

for TOOL in "llvm-tblgen" "mlir-tblgen" "mlir-linalg-ods-yaml-gen" "mlir-pdll" "llvm-config" "FileCheck"; do
  unzip -j wheelhouse/mlir-17.0.0*whl "mlir/bin/$TOOL" -d native_tools/
done

if [ x"$MATRIX_OS" == x"ubuntu-20.04" ]; then
  PLAT="manylinux_2_17"
elif [ x"$MATRIX_OS" == x"macos-11" ]; then
  PLAT="macosx_11_0"
elif [ x"$MATRIX_OS" == x"windows-2022" ]; then
  PLAT="win"
fi
PLAT=${PLAT}_$(echo $ARCH | tr '[:upper:]' '[:lower:]')
pushd native_tools
python setup.py bdist_wheel --dist-dir ../wheelhouse --plat $PLAT
popd

