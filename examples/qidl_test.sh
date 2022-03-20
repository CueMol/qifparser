#!/bin/bash

set -eux

INPUT_DIR=test_src
OUTPUT_DIR=build
TOP_DIR="$(cd $(dirname "$0")/..; pwd)"
PYTHON=${PYTHON:-'python3 -u'}

convert_file () {
INFILE=$1
OUTFILE=$2

$PYTHON $TOP_DIR/qifparser/main.py \
        -c $INFILE \
        -I $INPUT_DIR \
        -m cxx_src \
        -o $OUTFILE \
        --top_srcdir $INPUT_DIR \
        --top_builddir $OUTPUT_DIR
}

XXX=$(cd $INPUT_DIR; find . -name "*.qidl")
for i in $XXX ; do
    outfname=${i%.*}_wrap.cpp
    INFILE=$i
    OUTFILE=$outfname
    convert_file $INFILE $OUTFILE
done
