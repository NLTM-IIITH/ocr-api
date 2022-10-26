#!/bin/bash

# Given the set of params such as modality, language, and image data dir.
# this script will start the docker container which in turn will run the flask
# server and load the model specified by the params in the memory.


MODALITY="$1"
LANGUAGE="$2"
VERSION="v2_bilingual"
DATA_DIR="/home/ocr/website/images"

if [[ ! "$LANGUAGE" =~ ^(marathi|assamese|hindi|gujarati|gurumukhi|manipuri|bengali|oriya|punjabi|tamil|telugu|urdu|kannada|malayalam)$ ]]; then
	echo "Please enter a valid language (assamese, hindi, gujarati, gurumukhi, bengali, odia, punjabi, tamil, telugu, urdu, kannada, malayalam)"
	exit
fi

LANGUAGE="english_$(echo $LANGUAGE)"

if [[ ! "$MODALITY" =~ ^(handwritten|scene_text|printed)$ ]]; then
	echo "Please enter a valid modality (handwritten, scene_text, printed)"
	exit
fi


echo "Performing Inference for $LANGUAGE $MODALITY Task"

MODEL_DIR="/home/ajoy/0_ajoy_experiments/$MODALITY/3_trained_model/2_version_bilingual/$LANGUAGE"

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

CONTAINER_NAME="infer-$(echo $MODALITY)-$(echo $LANGUAGE)-$(echo $VERSION)"
echo "Starting the inference in detached docker container: $CONTAINER_NAME"

docker run --rm --name=$CONTAINER_NAME --gpus all --net host \
	-v $MODEL_DIR:/model:ro \
	-v $DATA_DIR:/data \
	ocr:v2_bilingual \
	python infer.py $LANGUAGE