MODALITY="$1"
LANGUAGE="$2"
DATA_DIR="$3"

echo "Performing Inference for $LANGUAGE $MODALITY Task"

MODEL_DIR="/home/ocr/models/pretrained/v3_iitb"

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
    -v $MODEL_DIR:/root/.cache/doctr/models \
	-v $MODEL_DIR:/models \
	-v $DATA_DIR:/data \
	ocr:v3_iitb \
	python infer.py -l $LANGUAGE -t $MODALITY
