cmake_minimum_required(VERSION 3.16)
project(caesar_hft LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(hft_core
    cpp/src/oms_core.cpp
)

target_include_directories(hft_core PUBLIC cpp/include)

enable_testing()

add_executable(oms_core_test cpp/tests/oms_core_test.cpp)
target_link_libraries(oms_core_test PRIVATE hft_core)
add_test(NAME oms_core_test COMMAND oms_core_test)
