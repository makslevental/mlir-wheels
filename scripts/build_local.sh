#!/usr/bin/env bash
set -xe
HERE=$(dirname "$(realpath $0)")

unameOut="$(uname -s)"
case "${unameOut}" in
    Linux*)     machine=linux;;
    Darwin*)    machine=macos;;
    CYGWIN*)    machine=windows;;
    MINGW*)     machine=windows;;
    MSYS_NT*)   machine=windows;;
    *)          machine="UNKNOWN:${unameOut}"
esac
echo ${machine}

export HOST_CCACHE_DIR="$(ccache --get-config cache_dir)"
ccache --show-stats
ccache --print-stats
ccache --show-config

export BUILD_OPENMP=true
export BUILD_VULKAN=false

if [ "$machine" == "linux" ]; then
  export LLVM_PROJECT_MAIN_SRC_DIR=/project/llvm-project
  export MATRIX_OS=ubuntu-20.04
  export CIBW_ARCHS=x86_64
  export ARCH=x86_64
  export PARALLEL_LEVEL=15
  export BUILD_CUDA=true
elif [ "$machine" == "macos" ]; then
  export LLVM_PROJECT_MAIN_SRC_DIR=$HERE/../llvm-project
  export MATRIX_OS=macos-11
  export CIBW_ARCHS=arm64
  export ARCH=arm64
  export PARALLEL_LEVEL=32
  export BUILD_CUDA=false
else
  export LLVM_PROJECT_MAIN_SRC_DIR=$HERE/../llvm-project
  export MATRIX_OS=windows-2022
  export CIBW_ARCHS=AMD64
  export ARCH=AMD64
  export BUILD_CUDA=false
fi

#export PIP_NO_BUILD_ISOLATION=false
cibuildwheel $HERE/.. --platform $machine

if [ x"$MATRIX_OS" == x"ubuntu-20.04" ]; then
  ccache -s
  rm -rf $HOST_CCACHE_DIR
  mv $HERE/../wheelhouse/.ccache $HOST_CCACHE_DIR
  ls -la $HOST_CCACHE_DIR
  ccache --show-stats
  ccache --print-stats
  ccache --show-config
fi

for TOOL in "llvm-tblgen" "mlir-tblgen" "mlir-linalg-ods-yaml-gen" "mlir-pdll" "llvm-config" "FileCheck"; do
  if [ x"$MATRIX_OS" == x"windows-2022" ]; then
    TOOL="$TOOL.exe"
  fi
  unzip -j $HERE/../wheelhouse/mlir-17.0.0*whl "mlir/bin/$TOOL" -d $HERE/../native_tools/
done

if [ x"$MATRIX_OS" == x"ubuntu-20.04" ]; then
  PLAT="manylinux_2_17"
elif [ x"$MATRIX_OS" == x"macos-11" ]; then
  PLAT="macosx_11_0"
elif [ x"$MATRIX_OS" == x"windows-2022" ]; then
  PLAT="win"
fi

PLAT=${PLAT}_$(echo $ARCH | tr '[:upper:]' '[:lower:]')
pushd $HERE/../native_tools
python setup.py bdist_wheel --dist-dir ../wheelhouse --plat $PLAT
popd

unzip $HERE/../wheelhouse/mlir-17.0.0*whl "mlir/python_packages/mlir_core/mlir/*" -d /tmp
cp -R /tmp/mlir/python_packages/mlir_core/mlir $HERE/../python_bindings
cibuildwheel $HERE/../python_bindings --platform $machine --output-dir $HERE/../wheelhouse
