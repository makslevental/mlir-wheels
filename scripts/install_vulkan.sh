#!/usr/bin/env bash
set -xe

if [[ x"$BUILD_VULKAN" == x"true" ]]; then
  if [ x"$MATRIX_OS" == x"macos-11" ]; then
    wget -q https://sdk.lunarg.com/sdk/download/1.3.239.0/mac/vulkansdk-macos-1.3.239.0.dmg
    sudo hdiutil attach vulkansdk-macos-1.3.239.0.dmg
    sudo /Volumes/vulkansdk-macos-1.3.239.0/InstallVulkan.app/Contents/MacOS/InstallVulkan \
      --accept-licenses \
      --default-answer \
      --confirm-command install \
      com.lunarg.vulkan.core \
      com.lunarg.vulkan.usr \
      com.lunarg.vulkan.sdl2 \
      com.lunarg.vulkan.glm \
      com.lunarg.vulkan.volk \
      com.lunarg.vulkan.vma
  else
    # compile and install vulkan-headers
    git clone -b v1.3.239 https://github.com/KhronosGroup/Vulkan-Headers.git
    mkdir build-vulkan-headers
    cmake G Ninja \
      -B build-vulkan-headers \
      -S Vulkan-Headers
    cmake --build build-vulkan-headers --target install

    # compile and install vulkan-loader
    git clone -b v1.3.239 https://github.com/KhronosGroup/Vulkan-Loader.git
    mkdir build-vulkan-loader
    cmake -G Ninja \
      -DBUILD_WSI_XCB_SUPPORT=0 \
      -DBUILD_WSI_XLIB_SUPPORT=0 \
      -DBUILD_WSI_WAYLAND_SUPPORT=0 \
      -DBUILD_WSI_DIRECTFB_SUPPORT=0 \
      -DBUILD_WSI_SCREEN_QNX_SUPPORT=0 \
      -B build-vulkan-loader \
      -S Vulkan-Loader
    cmake --build build-vulkan-loader --target install
  fi
fi