#!/usr/bin/env bash
set -xe
HERE=$(dirname "$(realpath "$0")")

unameOut="$(uname -s)"
case "${unameOut}" in
    Linux*)     machine=linux;;
    Darwin*)    machine=macos;;
    CYGWIN*)    machine=windows;;
    MINGW*)     machine=windows;;
    MSYS_NT*)   machine=windows;;
    *)          machine="UNKNOWN:${unameOut}"
esac
echo "${machine}"

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
ccache --show-stats
ccache --print-stats
ccache --show-config

if [ x"$BUILD_CUDA" == x"true" ] && [ ! -f "$HERE/../cuda_12.2.0_535.54.03_linux.run" ]; then
  wget -q https://developer.download.nvidia.com/compute/cuda/12.2.0/local_installers/cuda_12.2.0_535.54.03_linux.run -o "$HERE/../cuda_12.2.0_535.54.03_linux.run"
fi

export HOST_CCACHE_DIR="$(ccache --get-config cache_dir)"
cibuildwheel "$HERE"/.. --platform "$machine"

rename 's/cp311-cp311/py3-none/' "$HERE/../wheelhouse/"mlir-*whl

if [ -d "$HERE/../wheelhouse/.ccache" ]; then
  cp -R "$HERE/../wheelhouse/.ccache/"* "$HOST_CCACHE_DIR/"
fi

for TOOL in "llvm-tblgen" "mlir-tblgen" "mlir-linalg-ods-yaml-gen" "mlir-pdll" "llvm-config" "FileCheck"; do
  if [ x"$MATRIX_OS" == x"windows-2022" ]; then
    TOOL="$TOOL.exe"
  fi
  unzip -j "$HERE/../wheelhouse/"mlir-*whl "mlir/bin/$TOOL" -d "$HERE/../native_tools/"
done

if [ x"$MATRIX_OS" == x"ubuntu-20.04" ]; then
  PLAT="manylinux_2_17"
elif [ x"$MATRIX_OS" == x"macos-11" ]; then
  PLAT="macosx_11_0"
elif [ x"$MATRIX_OS" == x"windows-2022" ]; then
  PLAT="win"
fi

PLAT=${PLAT}_$(echo $ARCH | tr '[:upper:]' '[:lower:]')
pushd "$HERE/../native_tools"
python setup.py bdist_wheel --dist-dir ../wheelhouse --plat "$PLAT"
popd

unzip $HERE/../wheelhouse/mlir-*whl -x "mlir/bin/*" -d $HERE/../python_bindings

cp -R "$HERE/../scripts" "$HERE/../python_bindings"

pushd "$HERE/../python_bindings"
sed -i.bak 's/FATAL_ERROR/WARNING/g' mlir/lib/cmake/mlir/MLIRTargets.cmake
sed -i.bak 's/FATAL_ERROR/WARNING/g' mlir/lib/cmake/llvm/LLVMExports.cmake

find mlir -exec touch {} \;
cibuildwheel --platform "$machine" --output-dir ../wheelhouse
