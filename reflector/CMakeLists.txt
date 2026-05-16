######################################################################
##        Copyright (c) 2022 Carsten Wulff Software, Norway
## ###################################################################
## Created       : wulff at 2022-5-28
## ###################################################################
##  The MIT License (MIT)
##
##  Permission is hereby granted, free of charge, to any person obtaining a copy
##  of this software and associated documentation files (the "Software"), to deal
##  in the Software without restriction, including without limitation the rights
##  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
##  copies of the Software, and to permit persons to whom the Software is
##  furnished to do so, subject to the following conditions:
##
##  The above copyright notice and this permission notice shall be included in all
##  copies or substantial portions of the Software.
##
##  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
##  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
##  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
##  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
##  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
##  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
##  SOFTWARE.
##
######################################################################


cmake_minimum_required(VERSION 3.20.0)

find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(reflector)

if(NOT DEFINED DM_REFLECTOR_TIMEOUT_US)
  set(DM_REFLECTOR_TIMEOUT_US 500000)
endif()
if(NOT DEFINED DM_INITIATOR_TIMEOUT_US)
  set(DM_INITIATOR_TIMEOUT_US 50000)
endif()

zephyr_include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../common/include)
target_compile_definitions(app PRIVATE
  DM_REFLECTOR_TIMEOUT_US=${DM_REFLECTOR_TIMEOUT_US}
  DM_INITIATOR_TIMEOUT_US=${DM_INITIATOR_TIMEOUT_US}
)
target_sources(app PRIVATE  src/main.c)
