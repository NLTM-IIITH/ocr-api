#!/bin/bash

# Given the set of params such as modality, language, and image data dir.
# this script will start the docker container which in turn will run the flask
# server and load the model specified by the params in the memory.


MODALITY="$1"
LANGUAGE="$2"
DATA_DIR="$3"
VERSION="$4"


echo "Performing Inference for $VERSION $LANGUAGE $MODALITY Task"

MODEL_DIR="/home/ocr/models/pretrained/$VERSION/$MODALITY/$LANGUAGE"

if [ ! -d "$MODEL_DIR" ]; then
	echo "$MODEL_DIR : No such Directory"
	exit
else
	echo -e "MODEL_DIR\t$MODEL_DIR"
fi

if [ ! -d "$DATA_DIR" ]; then
	echo "$DATA_DIR : Enter a valid data directory"
	exit
else
	echo -e "DATA_DIR\t$DATA_DIR"
fi

docker run --rm --gpus all --net host \
	-v $MODEL_DIR:/model:ro \
	-v $DATA_DIR:/data \
	ocr:$VERSION \
	python infer.py $MODALITY $LANGUAGE
