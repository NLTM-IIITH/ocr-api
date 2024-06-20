from subprocess import call
from tempfile import TemporaryDirectory

from fastapi import APIRouter

from server.helper import process_images, process_ocr_output

from .models import OCRImageResponse, OCRRequest

router = APIRouter(
    prefix='/ocr/cegis',
    tags=['CEGIS Project'],
)


@router.post(
    '/',
    response_model=list[OCRImageResponse],
    response_model_exclude_none=True
)
def infer_ocr(ocr_request: OCRRequest) -> list[OCRImageResponse]:
    tmp = TemporaryDirectory(prefix='ocr_cegis')
    process_images(ocr_request.images, tmp.name)
    call(f'./cegis_infer.sh {tmp.name}', shell=True)
    return process_ocr_output(tmp.name)


@router.post(
    '/v2',
    response_model=list[OCRImageResponse],
    response_model_exclude_none=True
)
def shaon_infer_ocr(ocr_request: OCRRequest) -> list[OCRImageResponse]:
    tmp = TemporaryDirectory(prefix='ocr_cegis')
    process_images(ocr_request.images, tmp.name)
    call(f'./cegis_infer_v2.sh {tmp.name}', shell=True)
    return process_ocr_output(tmp.name)

@router.post(
    '/v3',
    response_model=list[OCRImageResponse],
    response_model_exclude_none=True
)
def cegis_v3_english_char_ocr(ocr_request: OCRRequest) -> list[OCRImageResponse]:
    """
    **ResNet18** model trained by Ajoy and deployed on March 21, 2023
    """
    tmp = TemporaryDirectory(prefix='ocr_cegis')
    process_images(ocr_request.images, tmp.name)
    call(f'./cegis_infer_v3.sh {tmp.name}', shell=True)
    return process_ocr_output(tmp.name)

@router.post(
    '/v4',
    response_model=list[OCRImageResponse],
    response_model_exclude_none=True
)
def cegis_v4_english_char_ocr(ocr_request: OCRRequest) -> list[OCRImageResponse]:
    """
    **ResNet50** model trained by Ajoy and deployed on March 21, 2023
    """
    tmp = TemporaryDirectory(prefix='ocr_cegis')
    process_images(ocr_request.images, tmp.name)
    call(f'./cegis_infer_v4.sh {tmp.name}', shell=True)
    return process_ocr_output(tmp.name)


@router.post(
    '/v5',
    response_model=list[OCRImageResponse],
    response_model_exclude_none=True
)
def cegis_v5_ocr(ocr_request: OCRRequest) -> list[OCRImageResponse]:
    """
    **??** model trained by Jasjeeet and deployedd on April 24, 2023
    """
    tmp = TemporaryDirectory(prefix='ocr_cegis')
    process_images(ocr_request.images, tmp.name)
    call(f'./cegis_infer_v4.sh {tmp.name}', shell=True)
    return process_ocr_output(tmp.name)


@router.post(
    '/v6',
    response_model=list[OCRImageResponse],
    response_model_exclude_none=True
)
def cegis_v6_ocr(ocr_request: OCRRequest) -> list[OCRImageResponse]:
    """
    TrOCR based model trained by Jasjeeet and deployedd on June 19, 2023
    """
    tmp = TemporaryDirectory(prefix='ocr_cegis')
    process_images(ocr_request.images, tmp.name)
    call(f'./cegis_infer_v6.sh {tmp.name}', shell=True)
    return process_ocr_output(tmp.name)