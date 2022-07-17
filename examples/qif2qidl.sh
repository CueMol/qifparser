#!/bin/bash

INPUT_DIR=~/proj64_cmake/cuemol2/src
OUTPUT_DIR=test_src

convert_file () {
INFILE=$1
OUTFILE=$2

cat  $INFILE | \
    tr -d "\r" | \
    sed -e 's/^\#[ ]*include/import/' | \
    sed -E '/^import/ s/$/;/' | \
    sed -E '/^import/ s/</"/' | \
    sed -E '/^import/ s/>/"/' | \
    sed -E '/^import/ s/\.qif/.qidl/' | \
    sed -E '/^import.*config\.h/d' | \
    sed -E '/^[ ]+uuid[ ]+/d' | \
    sed -E '/[a-zA-Z0-9_]+[ ]+uuid[ ]+/s/[ ]+uuid[^;]+//' | \
    sed -E '/^\#[^ ]+/d' > $OUTFILE
}

file_list=$(cd $INPUT_DIR; find . -name "*.qif")
for i in $file_list ; do
    outfname=${i%.*}.qidl
    INFILE=$INPUT_DIR/$i
    OUTFILE=$OUTPUT_DIR/$outfname
    OUTDIR=$(dirname $OUTFILE)
    mkdir -p $OUTDIR
    echo $OUTFILE
    convert_file $INFILE $OUTFILE
done

file_list=$(cd $INPUT_DIR; find . -name "*.moddef")
for i in $file_list ; do
    outfname=${i%.*}_mod.qidl
    INFILE=$INPUT_DIR/$i
    OUTFILE=$OUTPUT_DIR/$outfname
    OUTDIR=$(dirname $OUTFILE)
    mkdir -p $OUTDIR
    echo $OUTFILE
    convert_file $INFILE $OUTFILE
done

# remove unused files
rm $OUTPUT_DIR/qlib/ClassA.qidl
rm $OUTPUT_DIR/qlib/ClassB.qidl
rm $OUTPUT_DIR/qlib/ClassS.qidl
rm $OUTPUT_DIR/qlib/Vector4D.qidl

