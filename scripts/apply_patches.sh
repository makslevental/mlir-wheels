#!/usr/bin/env bash
set -uxo pipefail

# note that space before slash is important
PATCHES="\
add_td_to_mlirpythoncapi_headers \
cl_opt_name \
mscv \
register_test_pass \
remove_openmp_dep_on_clang_and_export_async_symbols \
tblgen \
"

if [[ x"${APPLY_PATCHES:-true}" == x"true" ]]; then
  for PATCH in $PATCHES; do
    echo "applying $PATCH"
    git apply --quiet --ignore-space-change --ignore-whitespace --directory llvm-project patches/$PATCH.patch
    ERROR=$?
    if [ $ERROR != 0 ]; then
      git apply --ignore-space-change --ignore-whitespace --verbose --directory llvm-project patches/$PATCH.patch -R --check
      ERROR=$?
      if [ $ERROR != 0 ]; then
        exit $ERROR
      fi
    fi
  done
fi
