from subprocess import call

from fastapi import APIRouter, Request

from .config import IMAGE_FOLDER
from .helper import (process_config, process_images, process_ocr_output,
                     save_logs)
from .models import OCRRequest, OCRResponse

router = APIRouter(
	prefix='/ocr/iitb',
	tags=['IITB Models'],
)

@router.post(
	'/v2',
	response_model=OCRResponse,
	response_model_exclude_none=True
)
async def infer_ocr(ocr_request: OCRRequest, request: Request) -> OCRResponse:
	process_images(ocr_request.image)
	lcode, _, modality, _ = process_config(ocr_request.config)

	if modality=='handwritten':
		call(f'./infer_iitb_v2.sh {modality} {lcode} {IMAGE_FOLDER}', shell=True)
		ret = process_ocr_output(lcode, modality, IMAGE_FOLDER)
		await save_logs(request, ret)
		return ret
	if modality=='printed':
		call(f'./infer_iitb_v2.sh {modality} {lcode} {IMAGE_FOLDER}', shell=True)
		ret = process_ocr_output(lcode, modality, IMAGE_FOLDER)
		await save_logs(request, ret)
		return ret
