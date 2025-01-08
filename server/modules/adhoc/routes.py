import json
import os
import shutil
import uuid
from datetime import datetime
from os.path import exists, join
from subprocess import call

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from server.config import LANGUAGES
from server.dependencies import save_uploaded_images
from server.helper import process_ocr_output, verify_model
from server.models import OCRImageResponse

router = APIRouter(
    prefix='/ocr/adhoc',
    tags=['ADHOC OCR APIs'],
)



def get_adhoc_models():
    with open('/home/ocr/models/adhoc_models.json', 'r') as f:
        return json.load(f)

def save_adhoc_models(data):
    with open('/home/ocr/models/adhoc_models.json', 'w') as f:
        json.dump(data, f, indent=4)


@router.post('/test')
async def test_adhoc_model(
    images: list[UploadFile] = Depends(save_uploaded_images),
    language: str = Form(...),
    modality: str = Form(...),
    version: str = Form(...),
) -> list[OCRImageResponse]:
    print(language, version, modality)
    verify_model(language, version, modality)
    if 'bilingual' in version:
        language = f'english_{language}'
    print(language, version, modality)
    folder = '/home/ocr/website/images'
    print(modality, language, folder, version)
    call(
        f'/home/ocr/website/infer.sh {modality} {language} {folder} {version}',
        shell=True
    )
    return process_ocr_output(folder)


@router.post('/')
async def create_adhoc_model(
    pretrained: UploadFile = File(...),
    base_model: str = Form(...),
    language: str = Form(...),
    modality: str = Form(...),
    user: str = Form(...),
    description: str = Form(...),
):
    code_path = '/home/ocr/models/code'
    pretrained_path = '/home/ocr/models/pretrained'
    try:
        assert language in LANGUAGES.values(), (
            'Invalid language code'
        )
        assert modality in ('printed', 'handwritten', 'scenetext'), (
            'Invalid modality'
        )
        assert exists(join(code_path, base_model)) \
            and exists(join(pretrained_path, base_model)), (
                'Invalid base_model specified'
            )
    except AssertionError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )
    version = f'adhoc_{str(uuid.uuid4())[:8]}'
    adhoc_models = get_adhoc_models()
    while version in adhoc_models.keys():
        version = f'adhoc_{str(uuid.uuid4())[:8]}'
    pretrained_path = join(
        pretrained_path,
        version,
        modality,
        language,
        'out', 'crnn_results'
    )
    os.makedirs(pretrained_path)
    with open(join(pretrained_path, 'best_cer.pth'), 'wb+') as f:
        shutil.copyfileobj(pretrained.file, f)
    os.system('docker build -t ocr:{} {}'.format(
        version,
        join(code_path, base_model),
    ))
    out = {
        'version': version,
        'language': language,
        'modality': modality,
        'user': user,
        'description': description,
        'timestamp': str(datetime.now()),
    }
    adhoc_models.update({
        version: out
    })
    save_adhoc_models(adhoc_models)
    return out

@router.get('/')
async def get_all_adhoc_models():
    return get_adhoc_models()

@router.delete('/')
async def delete_adhoc_model(
    version: str
):
    models = get_adhoc_models()
    if not version.startswith('adhoc_') or version not in models:
        raise HTTPException(
            status_code=400,
            detail=f'No Adhoc model found with version: {version}'
        )
    os.system(f'docker rmi ocr:{version}')
    pretrained_path = '/home/ocr/models/pretrained'
    os.system('mv {} {}'.format(
        join(pretrained_path, version),
        join(pretrained_path, 'archived_adhoc_models')
    ))
    del models[version]
    save_adhoc_models(models)
    return {'status': 'OK'}
