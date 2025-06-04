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

# rsync -avpP --exclude .git --exclude cmake-build-debug --exclude cmake-build-release ../../llvm/* llvm-project/

export BUILD_OPENMP=true
export BUILD_VULKAN=false
export BUILD_CUDA=false
export BUILD_AMDGPU=false
export APPLY_PATCHES=true
export DEBUG_CI_FAST_BUILD=false

if [ "$machine" == "linux" ]; then
  export MATRIX_OS=ubuntu-22.04
  export CIBW_ARCHS=x86_64
  export CIBW_BUILD=cp311-manylinux_x86_64
  export ARCH=x86_64
  export PARALLEL_LEVEL=15
elif [ "$machine" == "macos" ]; then
  export MATRIX_OS=macos-13
  export CIBW_ARCHS=arm64
  export CIBW_BUILD=cp311-macosx_arm64
  export ARCH=arm64
  export PARALLEL_LEVEL=32
else
  export MATRIX_OS=windows-2022
  export CIBW_ARCHS=AMD64
  export CIBW_BUILD=cp311-win_amd64
  export ARCH=AMD64
fi

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

if [ x"$MATRIX_OS" == x"ubuntu-22.04" ]; then
  PLAT="manylinux_2_17"
elif [ x"$MATRIX_OS" == x"macos-13" ]; then
  PLAT="macosx_12_0"
elif [ x"$MATRIX_OS" == x"windows-2022" ]; then
  PLAT="win"
fi

PLAT=${PLAT}_$(echo $ARCH | tr '[:upper:]' '[:lower:]')
pushd "$HERE/../native_tools"
python setup.py bdist_wheel --dist-dir ../wheelhouse --plat "$PLAT"
popd

cp -R "$HERE/../scripts" "$HERE/../python_bindings"
cp -R "$HERE/../wheelhouse" "$HERE/../python_bindings"

pushd "$HERE/../python_bindings"

cibuildwheel --platform "$machine" --output-dir ../wheelhouse
