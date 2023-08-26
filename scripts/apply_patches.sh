#!/usr/bin/env bash
set -xe

# note that space before slash is important
PATCHES="\
add_td_to_mlirpythoncapi_headers \
remove_openmp_dep_on_clang_and_export_async_symbols \
register_test_pass \
"

if [[ x"${APPLY_PATCHES}" == x"true" ]]; then
  for PATCH in $PATCHES; do
    echo "applying $PATCH"
    ls "$LLVM_PROJECT_MAIN_SRC_DIR"
    git apply --ignore-space-change --ignore-whitespace --verbose --directory llvm-project patches/$PATCH.patch
  done
fi

git apply --ignore-space-change --ignore-whitespace --verbose --directory llvm-project patches/mscv.patch