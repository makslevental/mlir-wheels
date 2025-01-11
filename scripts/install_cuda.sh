#!/usr/bin/env bash
set -xe

if [[ x"${BUILD_CUDA}" == x"true" ]]; then
  wget -q https://developer.download.nvidia.com/compute/cuda/12.6.3/local_installers/cuda_12.6.3_560.35.05_linux.run
  sh cuda_12.6.3_560.35.05_linux.run --toolkit --override --silent
  if [[ $? -ne 0 ]]; then
    echo "CUDA Installation Error."
    exit 1
  fi

  rm -rf cuda_12.6.3_560.35.05_linux.run

  CUDA_PATH=/usr/local/cuda
  echo "CUDA_PATH=${CUDA_PATH}"
  export CUDA_PATH=${CUDA_PATH}
  export PATH="$CUDA_PATH/bin:$PATH"
  export LD_LIBRARY_PATH="$CUDA_PATH/targets/x86_64-linux/lib/stubs:$LD_LIBRARY_PATH"
  if [[ -f "/etc/centos-release" ]] || [[ -f "/etc/almalinux-release" ]]; then
    yum install -y epel-release
    # sometimes the epel server is down. retry 5 times
    for i in $(seq 1 5); do
      yum install -y gcc-toolset-12 && s=0 && break || s=$? && sleep 15
    done
  fi
  export CC=/opt/rh/gcc-toolset-12/root/usr/bin/gcc
  export NVCC_CCBIN=/opt/rh/gcc-toolset-12/root/usr/bin/gcc
  export CXX=/opt/rh/gcc-toolset-12/root/usr/bin/g++
fi
