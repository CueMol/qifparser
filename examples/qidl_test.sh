#!/bin/bash

set -eux

INPUT_DIR=test_src
OUTPUT_DIR=build
TOP_DIR="$(cd $(dirname "$0")/..; pwd)"
PYTHON=${PYTHON:-'python3 -u'}

convert_file () {
INFILE=$1
OUTFILE=$2
MODE=$3

$PYTHON $TOP_DIR/qifparser/main.py \
        -c $INFILE \
        -I $INPUT_DIR \
        -m $MODE \
        -o $OUTFILE \
        --top_srcdir $INPUT_DIR \
        --top_builddir $OUTPUT_DIR
}

XXX=$(cd $INPUT_DIR; find . -name "*.qidl")
for i in $XXX ; do
    src_outfname=${i%.*}_wrap.cpp
    INFILE=$i
    convert_file $INFILE $src_outfname "cxx_src"
    hdr_outfname=${i%.*}_wrap.hpp
    convert_file $INFILE $hdr_outfname "cxx_hdr"
    break
done
