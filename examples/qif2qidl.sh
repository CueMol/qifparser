#!/bin/bash

INFILE=~/proj64_cmake/cuemol2/src/qsys/Scene.qif
OUTFILE=Scene.qidl

sed -e 's/^\#include/import/' $INFILE | \
    sed -E '/^import/ s/$/;/' | \
    sed -E '/^import/ s/</"/' | \
    sed -E '/^import/ s/>/"/' | \
    sed -E '/^\#[^ ]+/d' > $OUTFILE
