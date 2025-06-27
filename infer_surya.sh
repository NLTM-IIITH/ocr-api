#!/bin/bash

# Given the set of params such as modality, language, and image data dir.
# this script will start the docker container which in turn will run the flask
# server and load the model specified by the params in the memory.


LANGUAGE="$1"
DATA_DIR="$2"


echo "Performing Inference for SuryaOCR $LANGUAGE Task"

MODEL_DIR="/home/ocr/models/pretrained/surya"

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
	-v $MODEL_DIR:/root/.cache/huggingface/hub \
	-v $DATA_DIR:/data \
	ocr:surya \
	python infer.py $LANGUAGE
