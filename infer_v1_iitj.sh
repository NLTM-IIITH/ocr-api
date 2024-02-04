#!/bin/bash

# Given the set of params such as modality, language, and image data dir.
# this script will start the docker container which in turn will run the flask
# server and load the model specified by the params in the memory.


MODALITY="$1"
LANGUAGE="$2"
VERSION="v1_st_iitj"
DATA_DIR="$3"


echo "Performing Inference for $VERSION $LANGUAGE $MODALITY Task"

#MODEL_DIR="/home/ocr/models/pretrained/$VERSION/$MODALITY/$LANGUAGE"
#DOCTR_DIR="/home/ocr/models/pretrained/$VERSION/doctr_cache"
MODEL_DIR="/DATA/ocr_team_2/devesh/coding/end-to-end/integration-with-iiith/ocr-api/models"

echo "Checking for model dir"
if [ ! -d "$MODEL_DIR" ]; then
	echo "$MODEL_DIR : No such Directory"
	exit
else
	echo -e "MODEL_DIR\t$MODEL_DIR"
fi

echo "Checking for data dir"
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
	python3 recognise.py -l $LANGUAGE -i /data -o /data -c /model/parseq
