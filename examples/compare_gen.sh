#!/bin/bash

convert_file () {
INFILE=$1
OUTFILE=$2

sed -E 's/^[ ]+//' $INFILE | \
    sed -E '/^\#include[ ]+\".+_wrap\.hpp\"/s/[\/a-zA-Z0-9_]+\///'| \
    sed -E '/^[ ]*\/\//d'| \
    sed -E '/^[ ]*$/d'| \
    sed -E '/^\#pragma/d'| \
    sed -E '/^\#endif/d'| \
    sed -E '/^\#define/d'| \
    sed -E '/^\#ifndef/d' > $OUTFILE
}

in1_dir=/Users/user/proj64/qifparser/build
in2_dir=/Users/user/proj64_cmake/cuemol2/src

in1_files=$(cd $in1_dir; find . -name "*_wrap.?pp")
# echo $in1_files

for fn in $in1_files ; do
    in1="$in1_dir/$fn"
    in2="$in2_dir/$fn"

    if [ ! -e $in2 ]; then
        continue
    fi    

    tmpfile1=$(mktemp)
    tmpfile2=$(mktemp)
    
    convert_file $in1 $tmpfile1
    convert_file $in2 $tmpfile2
    
    #echo $tmpfile1 $tmpfile2
    diff_res=$(diff $tmpfile1 $tmpfile2)
    if [ -n "$diff_res" ]; then
        echo "=========="
        echo "in1: " $in1
        echo "in2: " $in2
        diff $tmpfile1 $tmpfile2
    fi    
    
    rm $tmpfile1 $tmpfile2

done
# in1=/Users/user/proj64_cmake/cuemol2/src/qlib/ByteArray_wrap.cpp
# in2=/Users/user/proj64/qifparser/build/qlib/ByteArray_wrap.cpp

# tmpfile1=$(mktemp)
# tmpfile2=$(mktemp)

# convert_file $in1 $tmpfile1
# convert_file $in2 $tmpfile2

# #echo $tmpfile1 $tmpfile2
# diff $tmpfile1 $tmpfile2

# rm $tmpfile1 $tmpfile2
