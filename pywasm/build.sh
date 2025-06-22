#!/bin/bash

pip download  mlir_native_tools -f https://makslevental.github.io/wheels
unzip -o -j mlir_native_tools-*whl -d mlir_native_tools
rm -rf mlir_native_tools-*whl
export LLVM_NATIVE_TOOL_DIR="$PWD/mlir_native_tools"
export LLVM_TABLEGEN="$PWD/mlir_native_tools/llvm-tblgen"
export MLIR_TABLEGEN="$PWD/mlir_native_tools/mlir-tblgen"
export MLIR_LINALG_ODS_YAML_GEN="$PWD/mlir_native_tools/mlir-linalg-ods-yaml-gen"
pyodide build . -o wheelhouse --compression-level 10
