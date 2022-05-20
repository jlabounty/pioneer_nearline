#!/bin/bash

# get the github environment
THISDIR=`git rev-parse --show-toplevel`
echo "Your github location: "$THISDIR

export PATH=$PATH:$THISDIR/analysis/master/build

# setup conda environment
eval "$(/home/pioneer/miniconda3/bin/conda shell.bash hook)" 
conda activate pioneer

echo "PIONEER Environment Setup Complete"