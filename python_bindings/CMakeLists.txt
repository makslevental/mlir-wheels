cmake_minimum_required(VERSION 3.13.4)

if(POLICY CMP0068)
  cmake_policy(SET CMP0068 NEW)
  set(CMAKE_BUILD_WITH_INSTALL_NAME_DIR ON)
endif()

if(POLICY CMP0075)
  cmake_policy(SET CMP0075 NEW)
endif()

if(POLICY CMP0077)
  cmake_policy(SET CMP0077 NEW)
endif()

if(POLICY CMP0091)
  cmake_policy(SET CMP0091 NEW)
endif()

if(POLICY CMP0116)
  cmake_policy(SET CMP0116 NEW)
endif()

if(POLICY CMP0135)
  cmake_policy(SET CMP0116 OLD)
endif()

project(PI LANGUAGES CXX C)

set(CMAKE_BUILD_WITH_INSTALL_NAME_DIR ON)

set(CMAKE_CXX_STANDARD
    17
    CACHE STRING "C++ standard to conform to")

if(MSVC)
  add_compile_options(
    $<$<CONFIG:>:/MT> # ---------|
    $<$<CONFIG:Debug>:/MTd> # ---|-- Statically link the runtime libraries
    $<$<CONFIG:Release>:/MT> # --|
  )
endif()

find_package(MLIR REQUIRED CONFIG)

message(STATUS "Using MLIRConfig.cmake in: ${MLIR_DIR}")
message(STATUS "Using LLVMConfig.cmake in: ${LLVM_DIR}")

set(LLVM_RUNTIME_OUTPUT_INTDIR ${CMAKE_BINARY_DIR}/bin)
set(LLVM_LIBRARY_OUTPUT_INTDIR ${CMAKE_BINARY_DIR}/lib)
set(MLIR_BINARY_DIR ${CMAKE_BINARY_DIR})

list(APPEND CMAKE_MODULE_PATH "${MLIR_CMAKE_DIR}")
list(APPEND CMAKE_MODULE_PATH "${LLVM_CMAKE_DIR}")
include(TableGen)
include(AddLLVM)
include(AddMLIR)
include(HandleLLVMOptions)

include_directories(${LLVM_INCLUDE_DIRS})
include_directories(${MLIR_INCLUDE_DIRS})
link_directories(${LLVM_BUILD_LIBRARY_DIR})
add_definitions(${LLVM_DEFINITIONS})

include(MLIRDetectPythonEnv)
include(AddMLIRPython)
mlir_detect_pybind11_install()
mlir_configure_python_dev_packages()

add_mlir_python_common_capi_library(
  MLIRPythonCAPI
  INSTALL_COMPONENT
  MLIRPythonModules
  INSTALL_DESTINATION
  mlir/_mlir_libs
  OUTPUT_DIRECTORY
  "${MLIR_BINARY_DIR}/mlir/_mlir_libs"
  RELATIVE_INSTALL_ROOT
  "../../../.."
  DECLARED_HEADERS
  MLIRPythonCAPI.HeaderSources
  DECLARED_SOURCES
  MLIRPythonSources
  MLIRPythonExtension.RegisterEverything
  ${_ADDL_TEST_SOURCES})

# ##############################################################################
# Custom targets.
# ##############################################################################

_flatten_mlir_python_targets(mlir_python_sources_deps MLIRPythonSources)
add_custom_target("mlir-python-sources" DEPENDS ${mlir_python_sources_deps})
if(NOT LLVM_ENABLE_IDE)
  add_llvm_install_targets(install-mlir-python-sources DEPENDS
                           mlir-python-sources COMPONENT mlir-python-sources)
endif()

# ##############################################################################
# The fully assembled package of modules. This must come last.
# ##############################################################################

add_mlir_python_modules(
  MLIRPythonModules
  ROOT_PREFIX
  "${MLIR_BINARY_DIR}/mlir"
  INSTALL_PREFIX
  "mlir"
  DECLARED_SOURCES
  MLIRPythonSources
  MLIRPythonExtension.RegisterEverything
  ${_ADDL_TEST_SOURCES}
  COMMON_CAPI_LINK_LIBS
  MLIRPythonCAPI)
