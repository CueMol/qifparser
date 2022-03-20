#!/bin/bash

set -eux

TOP_DIR="$(cd $(dirname "$0")/..; pwd)"
echo "TOP_DIR: $TOP_DIR"

TARGET=${1:-'ExampleClass'}
echo target: $TARGET

PYTHON=${PYTHON:-'python3 -u'}

$PYTHON $TOP_DIR/qifparser/main.py \
        -c $TOP_DIR/examples/${TARGET}.qidl \
        -I $TOP_DIR/examples \
        -I $TOP_DIR/examples/include \
        -m cxx_src \
        -o ${TARGET}_wrap.cpp \
        --top_srcdir $TOP_DIR \
        --top_builddir $TOP_DIR/build
