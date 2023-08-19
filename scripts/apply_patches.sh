#!/usr/bin/env bash
set -xe

patches=(
  add_td_to_mlirpythoncapi_headers.patch
  remove_openmp_dep_on_clang_and_export_async_symbols.patch
  register_test_pass.patch
)

for patch in "${patches[@]}"; do
  ls "$LLVM_PROJECT_MAIN_SRC_DIR"
  git apply --verbose --directory llvm-project patches/$patch --verbose
done
