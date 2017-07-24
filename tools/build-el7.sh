#!/bin/bash

git status | grep "nothing to commit" > /dev/null
if [ $? -ne 0 ];then
    echo "Please commit first !"
    exit 1
fi

# smartmgr
make clean all -C  ../
