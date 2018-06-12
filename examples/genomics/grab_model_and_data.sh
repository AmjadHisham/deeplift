#!/usr/bin/env bash

FILE="sequences.simdata.gz"
if [ ! -f "$FILE" ]
then
    wget https://raw.githubusercontent.com/AvantiShri/model_storage/5d2e2bffd66675fe9d26fdad2454a7faf6303a60/deeplift/genomics/keras2_conv1d_record_5_model_PQzyq_modelJson.json
else
    echo "File sequences.simdata.gz exists already"
fi

FILE="keras2_conv1d_record_5_model_PQzyq_modelJson.json"
if [ ! -f "$FILE" ]
then
    wget https://raw.githubusercontent.com/AvantiShri/model_storage/b6e1d69/deeplift/genomics/keras2_conv1d_record_5_model_PQzyq_modelJson.json
else
    echo "File keras2_conv1d_record_5_model_PQzyq_modelJson.json exists already"
fi

FILE="keras2_conv1d_record_5_model_PQzyq_modelWeights.h5"
if [ ! -f "$FILE" ]
then
    wget https://raw.githubusercontent.com/AvantiShri/model_storage/b6e1d69/deeplift/genomics/keras2_conv1d_record_5_model_PQzyq_modelWeights.h5
else
    echo "File keras2_record_5_model_PQzyq_modelWeights.h5 exists already"
fi

FILE="test.txt.gz"
if [ ! -f "$FILE" ]
then
    wget https://raw.githubusercontent.com/AvantiShri/model_storage/9aadb769735c60eb90f7d3d896632ac749a1bdd2/deeplift/genomics/test.txt.gz
else
    echo "File test.txt.gz exists already"
fi
