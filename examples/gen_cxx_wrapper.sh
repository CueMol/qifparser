#!/bin/bash

set -eux

TOP_DIR="$(cd $(dirname "$0")/..; pwd)"
echo "TOP_DIR: $TOP_DIR"

PYTHON=${PYTHON:-'python3 -u'}

$PYTHON $TOP_DIR/qifparser/main.py \
        -c $TOP_DIR/examples/example_class.qidl \
        -I $TOP_DIR/examples \
        -I $TOP_DIR/examples/include \
        -o example_class_wrap.cpp

