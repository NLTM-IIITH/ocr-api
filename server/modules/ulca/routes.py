from subprocess import call

from fastapi import APIRouter, Request

from .helper import (process_config, process_images, process_ocr_output,
                     save_logs)
from .models import OCRRequest, OCRResponse

router = APIRouter(
    prefix='/ocr/ulca',
    tags=['ULCA Models'],
)


@router.post(
    '/v2',
    response_model=OCRResponse,
    response_model_exclude_none=True
)
async def infer_ulca_v2_ocr_printed(ocr_request: OCRRequest, request: Request) -> OCRResponse:
    """
    This is the printed modality of the v2 ocr given to ulca.
    this was transfered to ulca on late sept and was online by first week oct.
    """
    process_images(ocr_request.image)
    lcode, language, modality, dlevel = process_config(ocr_request.config)
    call(f'./infer_ulca_v2.sh {modality} {language}', shell=True)
    ret = process_ocr_output(lcode, modality, dlevel)
    await save_logs(request, ret)
    return ret


@router.post(
    '/v3/printed',
    response_model=OCRResponse,
    response_model_exclude_none=True
)
async def infer_ulca_v3_ocr_printed(ocr_request: OCRRequest, request: Request) -> OCRResponse:
    """
    This is the printed modality of the v2 ocr given to ulca.
    this was transfered to ulca on late sept and was online by first week oct.
    """
    process_images(ocr_request.image)
    lcode, language, modality, dlevel = process_config(ocr_request.config)
    modality = 'printed'
    call(f'./infer_ulca_v3.sh {modality} {language}', shell=True)
    ret = process_ocr_output(lcode, modality, dlevel)
    await save_logs(request, ret)
    return ret


@router.post(
    '/v2/handwritten',
    response_model=OCRResponse,
    response_model_exclude_none=True
)
async def infer_ulca_v2_ocr_handwritten(ocr_request: OCRRequest, request: Request) -> OCRResponse:
    """
    This is the handwritten modality of the v2 ocr given to ulca.
    """
    process_images(ocr_request.image)
    lcode, language, modality, dlevel = process_config(ocr_request.config)
    modality = 'handwritten'
    call(f'./infer_ulca_v2.sh {modality} {language}', shell=True)
    ret = process_ocr_output(lcode, modality, dlevel)
    await save_logs(request, ret)
    return ret


@router.post(
    '/v2/scenetext',
    response_model=OCRResponse,
    response_model_exclude_none=True
)
async def infer_ulca_v2_ocr_scenetext(ocr_request: OCRRequest, request: Request) -> OCRResponse:
    """
    This is the handwritten modality of the v2 ocr given to ulca.
    """
    process_images(ocr_request.image)
    lcode, language, modality, dlevel = process_config(ocr_request.config)
    modality = 'scenetext'
    if language == 'malayalam':
        # This is due to unavailability of the scenetext malayalam model
        modality = 'printed'
    call(f'./infer_ulca_v2.sh {modality} {language}', shell=True)
    ret = process_ocr_output(lcode, modality, dlevel)
    await save_logs(request, ret)
    return ret