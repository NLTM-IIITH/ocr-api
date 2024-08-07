import base64
import os
import shutil
import uuid
from datetime import datetime
from os.path import join
from subprocess import call
from tempfile import TemporaryDirectory
from typing import List

from dateutil.tz import gettz
from fastapi import Depends, FastAPI, Form, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from server.config import IMAGE_FOLDER

from .database import close_mongo_connection, connect_to_mongo
from .dependencies import save_uploaded_images
from .helper import (call_page_pu, call_page_tesseract,
                     call_page_tesseract_pad, load_model, process_images,
                     process_language, process_modality, process_ocr_output,
                     process_version, verify_model)
from .models import (LanguageEnum, ModalityEnum, OCRImageResponse, OCRRequest,
                     VersionEnum)
from .modules.auth.dependencies import get_active_user
from .modules.auth.models import User
from .modules.auth.routes import router as auth_router
from .modules.cegis.routes import router as cegis_router
from .modules.core.models import Log
from .modules.external.routes import router as external_router
from .modules.iitb_v2.routes import router as iitb_v2_router
from .modules.ulca.routes import router as ulca_router

app = FastAPI(
    title='OCR API',
    docs_url='/ocr/docs',
    openapi_url='/ocr/openapi.json'
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*'],
    allow_credentials=True,
)

app.add_event_handler('startup', connect_to_mongo)
app.add_event_handler('shutdown', close_mongo_connection)

app.include_router(cegis_router)
app.include_router(ulca_router)
app.include_router(external_router)
app.include_router(iitb_v2_router)
app.include_router(auth_router)



@app.middleware('http')
async def log_request_timestamp(request: Request, call_next):
    local_tz = gettz('Asia/Kolkata')
    print(f'Received request at: {datetime.now(tz=local_tz).isoformat()} for {request.url} from {request.client}')
    ret = await call_next(request)
    return ret


@app.get('/ocr/ping', tags=['Testing'])
def test_server_online():
    return 'pong'


def save_uploaded_image(image: UploadFile) -> str:
    """
    function to save the uploaded image to the disk

    @returns the absolute location of the saved image
    """
    print('removing all the previous uploaded files from the image folder')
    os.system(f'rm -rf {IMAGE_FOLDER}/*')
    location = join(IMAGE_FOLDER, '{}.{}'.format(
        str(uuid.uuid4()),
        image.filename.strip().split('.')[-1]
    ))
    with open(location, 'wb+') as f:
        shutil.copyfileobj(image.file, f)
    return location


@app.post(
    '/ocr/word',
    tags=['OCR'],
    response_model=List[OCRImageResponse],
    response_model_exclude_none=True
)
async def authenticated_infer_ocr(
    ocr_request: OCRRequest,
    user: User = Depends(get_active_user),
) -> List[OCRImageResponse]:
    print(f'[{user.username}] Calling Authenticated OCR')
    tmp = TemporaryDirectory(prefix='ocr_images')
    image_count = process_images(ocr_request.imageContent, tmp.name)

    lcode, language = process_language(ocr_request.language)
    version = process_version(ocr_request.version)
    modality = process_modality(ocr_request.modality)
    print(f'[{user.username}] before verification', language, version, modality)
    verify_model(language, version, modality)
    if 'bilingual' in version or version.startswith('parliament'):
        language = f'english_{language}'
    print(f'[{user.username}]', language, version, modality)
    if version == 'v0':
        load_model(modality, language, version)
        call(f'./infer_v0.sh {modality} {language}', shell=True)
    elif version == 'v1_iitb':
        call(f'./infer_v1_iitb.sh {modality} {language} {tmp.name}', shell=True)
    elif version == 'v2_iitb':
        call(f'./infer_v2_iitb.sh {modality} {lcode} {tmp.name}', shell=True)
    elif version == 'v3_iitb':
        call(f'./infer_v3_iitb.sh {modality} {lcode} {tmp.name}', shell=True)
    elif version == 'v1_pu':
        return await call_page_pu(language, tmp.name)
    elif version == 'v1_st_iitj':
        call(f'./infer_v1_iitj.sh {modality} {language} {tmp.name}')
    elif version == 'tesseract_pad':
        return call_page_tesseract_pad(language, tmp.name)
    elif version == 'tesseract':
        return call_page_tesseract(language, tmp.name)
    else:
        if ocr_request.meta.get('include_probability', False):
            call(
                f'./infer_prob.sh {modality} {language} {tmp.name} {version}',
                shell=True
            )
        else:
            call(
                f'./infer.sh {modality} {language} {tmp.name} {version}',
                shell=True
            )
    ret = process_ocr_output(tmp.name)
    await Log.create(
        version=version,
        user_token=user.id,
        language=language,
        modality=modality,
        image_count=image_count
    )
    return ret


@app.post(
    '/ocr/infer',
    tags=['OCR'],
    response_model=List[OCRImageResponse],
    response_model_exclude_none=True
)
async def infer_ocr(ocr_request: OCRRequest) -> List[OCRImageResponse]:
    tmp = TemporaryDirectory(prefix='ocr_images')
    image_count = process_images(ocr_request.imageContent, tmp.name)

    lcode, language = process_language(ocr_request.language)
    version = process_version(ocr_request.version)
    modality = process_modality(ocr_request.modality)
    print('before verification', language, version, modality)
    verify_model(language, version, modality)
    if 'bilingual' in version or version.startswith('parliament'):
        language = f'english_{language}'
    print(language, version, modality)
    if version == 'v0':
        load_model(modality, language, version)
        call(f'./infer_v0.sh {modality} {language}', shell=True)
    elif version == 'v1_iitb':
        call(f'./infer_v1_iitb.sh {modality} {language} {tmp.name}', shell=True)
    elif version == 'v2_iitb':
        call(f'./infer_v2_iitb.sh {modality} {lcode} {tmp.name}', shell=True)
    elif version == 'v3_iitb':
        call(f'./infer_v3_iitb.sh {modality} {lcode} {tmp.name}', shell=True)
    elif version == 'V-03.02.00.01':
        call(f'./infer_new_iitb.sh {modality} {lcode} {tmp.name}', shell=True)
    elif version == 'v1_pu':
        return await call_page_pu(language, tmp.name)
    elif version == 'v1_st_iitj':
        call(f'./infer_v1_iitj.sh {modality} {language} {tmp.name}')
    elif version == 'tesseract_pad':
        return call_page_tesseract_pad(language, tmp.name)
    elif version == 'tesseract':
        return call_page_tesseract(language, tmp.name)
    else:
        if ocr_request.meta.get('include_probability', False):
            call(
                f'./infer_prob.sh {modality} {language} {tmp.name} {version}',
                shell=True
            )
        else:
            call(
                f'./infer.sh {modality} {language} {tmp.name} {version}',
                shell=True
            )
    ret = process_ocr_output(tmp.name)
    await Log.create(
        version=version,
        language=language,
        modality=modality,
        image_count=image_count
    )
    return ret


@app.post(
    '/ocr/test',
    tags=['Test OCR'],
    response_model=List[OCRImageResponse],
    response_model_exclude_none=True
)
async def infer_test_ocr(
    images: List[UploadFile] = Depends(save_uploaded_images),
    language: LanguageEnum = Form(LanguageEnum.hi),
    modality: ModalityEnum = Form(ModalityEnum.printed),
    version: VersionEnum = Form(VersionEnum.v2),
) -> List[OCRImageResponse]:
    print(images)
    lcode, language = process_language(language)
    version = process_version(version)
    modality = process_modality(modality)

    verify_model(language, version, modality)
    if 'bilingual' in version:
        language = f'english_{language}'
    print(language, version, modality)
    folder = '/home/ocr/website/images'
    if version == 'v0':
        load_model(modality, language, version)
        call(f'./infer_v0.sh {modality} {language}', shell=True)
    elif version == 'v5_urdu':
        call(
            f'./infer.sh printed urdu {folder} v5_urdu',
            shell=True
        )
    elif version == 'v1_iitb':
        call(f'./infer_v1_iitb.sh {modality} {language} {folder}', shell=True)
    elif version == 'v2_iitb':
        call(f'./infer_v2_iitb.sh {modality} {lcode} {folder}', shell=True)
    elif version == 'v3_iitb':
        call(f'./infer_v3_iitb.sh {modality} {lcode} {folder}', shell=True)
    elif version == 'V-03.02.00.01':
        call(f'./infer_new_iitb.sh {modality} {lcode} {folder}', shell=True)
    elif version == 'v1_pu':
        return await call_page_pu(language, folder)
    elif version == 'tesseract':
        # call_tesseract(language, folder)
        return call_page_tesseract(language, folder)
    else:
        print(modality, language, folder, version)
        call(
            f'./infer.sh {modality} {language} {folder} {version}',
            shell=True
        )
    return process_ocr_output(folder)
