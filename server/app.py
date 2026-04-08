import asyncio
import os
import shutil
import uuid
from datetime import datetime
from os.path import join
from tempfile import TemporaryDirectory
from typing import List

from dateutil.tz import gettz
from fastapi import Depends, FastAPI, Form, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from server.config import IMAGE_FOLDER

from .database import close_mongo_connection, connect_to_mongo
from .dependencies import save_uploaded_images
from .helper import (call_new_iitd_api, call_new_iitd_v2_api,call_new_iitd_ci_api, call_page_pu,
                     call_page_pu_2, call_page_pu_3, call_page_tesseract,
                     call_page_tesseract_pad, call_sarvam_api, load_model,
                     process_images, process_language, process_modality,
                     process_ocr_output, process_version, verify_model)
from .models import (LanguageEnum, ModalityEnum, OCRImageResponse, OCRRequest,
                     VersionEnum)
from .modules.adhoc.routes import router as adhoc_router
from .modules.core.models import Log
from .modules.external.routes import router as external_router
from .modules.iitb_v2.routes import router as iitb_v2_router

# from .modules.auth.routes import router as auth_router
# from .modules.cegis.routes import router as cegis_router
# from .modules.postprocess.routes import router as postprocess_router
# from .modules.ulca.routes import router as ulca_router


async def run(command: str) -> int:
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()
    print(stdout.decode())
    return process.returncode

    async def read_stream(stream):
        while True:
            line = await stream.readline()
            if line:
                print(line.decode().rstrip())
            else:
                break

    # Start reading stdout and stderr concurrently
    await asyncio.gather(
        read_stream(process.stdout),
        read_stream(process.stderr)
    )

    returncode = await process.wait()
    return returncode



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



@app.middleware('http')
async def log_request_timestamp(request: Request, call_next):
    local_tz = gettz('Asia/Kolkata')
    print(f'Received request at: {datetime.now(tz=local_tz).isoformat()} for {request.url} from {request.client}')
    ret = await call_next(request)
    return ret



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
    verify_model(language, version, modality)
    if 'bilingual' in version or version.startswith('parliament'):
        language = f'english_{language}'
    print(language, version, modality, image_count)
    if version == 'v0':
        load_model(modality, language, version)
        await run(f'./infer_v0.sh {modality} {language}')
    elif version == 'v1_iitb':
        await run(f'./infer_v1_iitb.sh {modality} {language} {tmp.name}')
    elif version == 'v2_iitb':
        await run(f'./infer_v2_iitb.sh {modality} {lcode} {tmp.name}')
    elif version == 'v3_iitb':
        await run(f'./infer_v3_iitb.sh {modality} {lcode} {tmp.name}')
    elif version == 'V-03.02.00.01':
        await run(f'./infer_new_iitb2.sh {modality} {lcode} {tmp.name}')
    elif version == 'V-03.02.00.02':
        if language == 'sanskrit':
            return call_page_tesseract('sanskrit', tmp.name)
        await run(f'./infer_new_iitb2.sh {modality} {lcode} {tmp.name}')
    elif version == 'V-03.02.00.03':
        return call_page_tesseract(language, tmp.name)
    elif version == 'v1_pu':
        return await call_page_pu(language, tmp.name)
    elif version == 'v2_pu':
        return await call_page_pu_2(language, tmp.name)
    elif version == 'v3_pu':
        return await call_page_pu_3(language, tmp.name)
    elif version == 'v1_st_iitj':
        await run(f'./infer_v1_iitj.sh {modality} {language} {tmp.name}')
    elif version == 'tesseract_pad':
        return call_page_tesseract_pad(language, tmp.name)
    elif version == 'tesseract':
        return call_page_tesseract(language, tmp.name)
    elif version == 'V-02.01.00.01':
        return await call_new_iitd_api(ocr_request)
    elif version == 'V-02.01.00.02':
        return await call_new_iitd_v2_api(ocr_request)
    elif version == 'combined_indic_iitd':
        return await call_new_iitd_ci_api(ocr_request)
    elif version == 'sarvam':
        return await call_sarvam_api(lcode, tmp.name)
    else:
        if ocr_request.meta.get('include_probability', False):
            await run(
                f'./infer_prob.sh {modality} {language} {tmp.name} {version}'
            )
        else:
            await run(
                f'./infer.sh {modality} {language} {tmp.name} {version}'
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
    tags=['OCR'],
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
        await run(f'./infer_v0.sh {modality} {language}')
    elif version == 'v5_urdu':
        await run(
            f'./infer.sh printed urdu {folder} v5_urdu'
        )
    elif version == 'v1_iitb':
        await run(f'./infer_v1_iitb.sh {modality} {language} {folder}')
    elif version == 'v2_iitb':
        await run(f'./infer_v2_iitb.sh {modality} {lcode} {folder}')
    elif version == 'v3_iitb':
        await run(f'./infer_v3_iitb.sh {modality} {lcode} {folder}')
    elif version == 'V-03.02.00.01':
        await run(f'./infer_new_iitb.sh {modality} {lcode} {folder}')
    elif version == 'V-03.02.00.02':
        if language == 'sanskrit':
            return call_page_tesseract('sanskrit', folder)
        await run(f'./infer_new_iitb2.sh {modality} {lcode} {folder}')
    elif version == 'V-03.02.00.03':
        return call_page_tesseract(language, folder)
    elif version == 'v1_pu':
        return await call_page_pu(language, folder)
    elif version == 'v2_pu':
        return await call_page_pu_2(language, folder)
    elif version == 'v3_pu':
        return await call_page_pu_3(language, folder)
    elif version == 'tesseract':
        return call_page_tesseract(language, folder)
    elif version == 'sarvam':
        return await call_sarvam_api(lcode, folder)
    
    
    
    else:
        print(modality, language, folder, version)
        await run(
            f'./infer.sh {modality} {language} {folder} {version}'
        )
    return process_ocr_output(folder)


# app.include_router(cegis_router)
# app.include_router(ulca_router)
# app.include_router(auth_router)
# app.include_router(postprocess_router)
app.include_router(external_router)
app.include_router(iitb_v2_router)
app.include_router(adhoc_router)


@app.get('/ocr/ping', tags=['Testing'])
async def test_server_online():
    return 'pong'

@app.get('/ocr/populate', tags=['Testing'])
async def populate_db():
    """
    Function to populate the database with some initial data
    """
    from itertools import product

    from tqdm import tqdm

    from server.config import LANGUAGES
    from server.helper import verify_model
    from server.models import VersionEnum
    from server.modules.core.models import Model

    modalitys = ['printed', 'handwritten', 'scenetext']
    languages = list(LANGUAGES.values())
    versions = [i.value for i in list(VersionEnum)]
    a = list(product(languages, versions, modalitys))
    b = []
    for i in a:
        try:
            verify_model(*i)
            b.append(i)
        except:
            pass
    print(len(b))
    for i in tqdm(b):
        await Model.create(
            language=i[0],
            version=i[1],
            modality=i[2]
        )


Instrumentator().instrument(app).expose(app)
