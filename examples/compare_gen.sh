#!/bin/bash

convert_file () {
INFILE=$1
OUTFILE=$2

sed -E 's/^[ ]+//' $INFILE | \
    sed -E '/^[ ]*\/\//d'| \
    sed -E '/^[ ]*$/d'| \
    sed -E '/^\#pragma/d'| \
    sed -E '/^\#endif/d'| \
    sed -E '/^\#define/d'| \
    sed -E '/^\#ifndef/d' > $OUTFILE
}

in1=/Users/user/proj64_cmake/cuemol2/src/qlib/ByteArray_wrap.cpp
in2=/Users/user/proj64/qifparser/build/qlib/ByteArray_wrap.cpp

tmpfile1=$(mktemp)
tmpfile2=$(mktemp)

convert_file $in1 $tmpfile1
convert_file $in2 $tmpfile2

#echo $tmpfile1 $tmpfile2
diff -y $tmpfile1 $tmpfile2

rm $tmpfile1 $tmpfile2
