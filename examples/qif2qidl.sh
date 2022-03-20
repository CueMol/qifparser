#!/bin/bash

INPUT_DIR=~/proj64_cmake/cuemol2/src
OUTPUT_DIR=test_src

convert_file () {
INFILE=$1
OUTFILE=$2

sed -e 's/^\#include/import/' $INFILE | \
    sed -E '/^import/ s/$/;/' | \
    sed -E '/^import/ s/</"/' | \
    sed -E '/^import/ s/>/"/' | \
    sed -E '/^import/ s/\.qif/.qidl/' | \
    sed -E '/[ ]+uuid[ ]+/d' | \
    sed -E '/^\#[^ ]+/d' > $OUTFILE
}

XXX=$(cd $INPUT_DIR; find . -name "*.qif")
for i in $XXX ; do
    outfname=${i%.*}.qidl
    INFILE=$INPUT_DIR/$i
    OUTFILE=$OUTPUT_DIR/$outfname
    OUTDIR=$(dirname $OUTFILE)
    mkdir -p $OUTDIR
    echo $OUTFILE
    convert_file $INFILE $OUTFILE
done
