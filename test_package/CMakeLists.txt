cmake_minimum_required(VERSION 3.4 FATAL_ERROR)

project(wxwidgets_conan_test)
set(TARGET_NAME run_conan_test)


# Setup Conan
include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()


add_executable(${TARGET_NAME} main.cpp)

target_link_libraries(${TARGET_NAME} ${CONAN_LIBS})
