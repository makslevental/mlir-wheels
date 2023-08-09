#!/usr/bin/env bash
set -xe

if [[ x"${BUILD_CUDA}" == x"true" ]]; then
  wget -q https://developer.download.nvidia.com/compute/cuda/12.2.0/local_installers/cuda_12.2.0_535.54.03_linux.run
  sh cuda_12.2.0_535.54.03_linux.run --toolkit --silent --override
  if [[ $? -ne 0 ]]; then
    echo "CUDA Installation Error."
    exit 1
  fi

  rm -rf cuda_12.2.0_535.54.03_linux.run

  CUDA_PATH=/usr/local/cuda
  echo "CUDA_PATH=${CUDA_PATH}"
  export CUDA_PATH=${CUDA_PATH}
  export PATH="$CUDA_PATH/bin:$PATH"
  export LD_LIBRARY_PATH="$CUDA_PATH/lib:$LD_LIBRARY_PATH"
  export LD_LIBRARY_PATH="$CUDA_PATH/lib64:$LD_LIBRARY_PATH"
fi