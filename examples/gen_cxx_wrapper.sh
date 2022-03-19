#!/bin/bash

set -eux

TOP_DIR="$(cd $(dirname "$0")/..; pwd)"
echo "TOP_DIR: $TOP_DIR"

PYTHON=${PYTHON:-'python3 -u'}

$PYTHON $TOP_DIR/qifparser/main.py \
        -c examples/ExampleClass.qidl \
        -I $TOP_DIR/examples \
        -I $TOP_DIR/examples/include \
        -m cxx_src \
        -o ExampleClass_wrap.cpp \
        --top_srcdir $TOP_DIR \
        --top_builddir $TOP_DIR/build
