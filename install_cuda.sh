#!/usr/bin/env bash
set -xe

if [[ ! -z "${BUILD_CUDA}" ]]; then
  curl http://developer.download.nvidia.com/compute/cuda/11.7.1/local_installers/cuda_11.7.1_515.65.01_linux.run -o cuda.run
  sudo cuda.run --toolkit --silent --override
  if [[ $? -ne 0 ]]; then
    echo "CUDA Installation Error."
    exit 1
  fi

  CUDA_PATH=/usr/local/cuda
  echo "CUDA_PATH=${CUDA_PATH}"
  export CUDA_PATH=${CUDA_PATH}
  export PATH="$CUDA_PATH/bin:$PATH"
  export LD_LIBRARY_PATH="$CUDA_PATH/lib:$LD_LIBRARY_PATH"
  export LD_LIBRARY_PATH="$CUDA_PATH/lib64:$LD_LIBRARY_PATH"
fi