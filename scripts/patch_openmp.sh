#!/usr/bin/env bash
set -xe


if [[ x"$BUILD_OPENMP" == x"true" ]]; then
  if [ x"$MATRIX_OS" == x"macos-11" ]; then
    # this removes a transitive dependency on clang
    sed -i.bak 's/construct_check_openmp_target()//g' "$LLVM_PROJECT_MAIN_SRC_DIR/openmp/CMakeLists.txt"
    sed -i.bak 's/set(ENABLE_CHECK_TARGETS TRUE)//g' "$LLVM_PROJECT_MAIN_SRC_DIR/openmp/cmake/OpenMPTesting.cmake"
    sed -i.bak 's/extern "C"/extern "C" __attribute__((visibility("default")))/g' "$LLVM_PROJECT_MAIN_SRC_DIR/mlir/lib/ExecutionEngine/AsyncRuntime.cpp"
  else
    # this removes a transitive dependency on clang
    sed -i 's/construct_check_openmp_target()//g' "$LLVM_PROJECT_MAIN_SRC_DIR/openmp/CMakeLists.txt"
    sed -i 's/set(ENABLE_CHECK_TARGETS TRUE)//g' "$LLVM_PROJECT_MAIN_SRC_DIR/openmp/cmake/OpenMPTesting.cmake"
    sed -i 's/extern "C"/extern "C" __attribute__((visibility("default")))/g' "$LLVM_PROJECT_MAIN_SRC_DIR/mlir/lib/ExecutionEngine/AsyncRuntime.cpp"
  fi
fi