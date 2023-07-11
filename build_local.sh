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
export PARALLEL_LEVEL=5
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
cibuildwheel --platform linux
