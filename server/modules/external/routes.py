import io
import shutil
import uuid
from os.path import join
from tempfile import TemporaryDirectory

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from google.cloud import translate_v2 as translate
from PIL import Image

from ..core.models import Log
from .dependencies import get_token
from .helper import (call_google_ocr, call_google_tts, call_page_azure,
                     call_page_easyocr, call_page_easyocr_bulk,
                     call_page_surya, call_page_tesseract2,
                     call_page_tesseract_unbulk)
from .models import Token

router = APIRouter(
    prefix='/ocr',
    tags=['External OCR APIs'],
)


@router.post(
    '/easyocr',
)
async def infer_easy_ocr(
    image: UploadFile,
    language: str = Form('english'),
):
    tmp = TemporaryDirectory()
    location = join(tmp.name, '{}.{}'.format(
        str(uuid.uuid4()),
        image.filename.strip().split('.')[-1]
    ))
    with open(location, 'wb+') as f:
        shutil.copyfileobj(image.file, f)
    await Log.create(
        version='easyocr',
        language='',
        image_count=1
    )
    return call_page_easyocr(language, tmp.name)

@router.post(
    '/easyocr/bulk',
)
async def infer_easy_ocr_bulk(
    images: list[UploadFile],
    language: str = Form('english'),
):
    tmp = TemporaryDirectory()
    for idx, image in enumerate(images):
        location = join(tmp.name, '{}.{}'.format(
            str(idx),
            image.filename.strip().split('.')[-1]
        ))
        with open(location, 'wb') as f:
            shutil.copyfileobj(image.file, f)
    await Log.create(
        version='easyocr',
        language=language,
        image_count=len(images)
    )
    return call_page_easyocr_bulk(language, tmp.name)

@router.post(
    '/azure',
)
async def infer_azure_ocr(
    image: UploadFile,
):
    tmp = TemporaryDirectory()
    location = join(tmp.name, '{}.{}'.format(
        str(uuid.uuid4()),
        image.filename.strip().split('.')[-1]
    ))
    with open(location, 'wb+') as f:
        shutil.copyfileobj(image.file, f)
    await Log.create(
        version='azure',
        language='',
        image_count=1
    )
    return call_page_azure(location)


@router.post(
    '/surya'
)
async def infer_surya_ocr(
    image: UploadFile,
    language: str = Form('english'),
):
    tmp = TemporaryDirectory()
    location = join(tmp.name, '{}.{}'.format(
        str(uuid.uuid4()),
        image.filename.strip().split('.')[-1]
    ))
    with open(location, 'wb+') as f:
        shutil.copyfileobj(image.file, f)
    await Log.create(
        version='surya',
        language=language,
        image_count=1
    )
    return call_page_surya(language, tmp.name)


@router.post(
    '/tesseract/bulk',
)
async def infer_tesseract_ocr_bulk(
    images: list[UploadFile],
    language: str = Form('english'),
    bilingual: bool = Form(False),
    pad_a4: bool = Form(False)
):
    tmp = TemporaryDirectory()
    for image in images:
        location = join(tmp.name, '{}.{}'.format(
            str(uuid.uuid4()),
            image.filename.strip().split('.')[-1]
        ))
        if pad_a4:
            img = Image.open(io.BytesIO(await image.read()))
            new_img = Image.new('RGB', (2480,3508), (255,255,255))
            new_img.paste(img, (100, 100))
            new_img.convert('RGB').save(location)
        else:
            with open(location, 'wb') as f:
                shutil.copyfileobj(image.file, f)
    await Log.create(
        version='tesseract',
        language=language,
        image_count=1
    )
    return call_page_tesseract2(language, tmp.name, bilingual)

@router.post(
    '/tesseract',
)
async def infer_tesseract_ocr(
    image: UploadFile = File(...),
    language: str = Form('english'),
    bilingual: bool = Form(False),
    pad_a4: bool = Form(False)
):
    tmp = TemporaryDirectory()
    location = join(tmp.name, '{}.{}'.format(
        str(uuid.uuid4()),
        image.filename.strip().split('.')[-1]
    ))
    if pad_a4:
        img = Image.open(io.BytesIO(await image.read()))
        new_img = Image.new('RGB', (2480,3508), (255,255,255))
        new_img.paste(img, (100, 100))
        new_img.convert('RGB').save(location)
    else:
        with open(location, 'wb+') as f:
            shutil.copyfileobj(image.file, f)
    await Log.create(
        version='tesseract',
        language=language,
        image_count=1
    )
    return call_page_tesseract_unbulk(language, tmp.name, bilingual)


@router.get('/token', response_model=list[Token])
async def fetch_all_token(
    password: str
) -> list[Token]:
    if password == 'kkrishna':
        return await Token.all()
    else:
        raise HTTPException(
            status_code=400,
            detail='Invalid Password'
        )

@router.post('/token/refresh', response_model=Token)
async def fetch_all_token(
    id: str
) -> Token:
    tokens = await Token.filter(id=id)
    if tokens and len(tokens) == 1:
        token = tokens[0]
        await token.update(quota=1000)
        return await token.refresh()
    else:
        raise HTTPException(
            status_code=400,
            detail='Invalid ID'
        )


@router.post(
    '/external/token',
    response_model=Token
)
async def fetch_external_token(
    email: str = Form(''),
    purpose: str = Form(''),
) -> Token:
    existing_tokens = await Token.filter(email=email)
    if existing_tokens:
        return existing_tokens[0]
    token = Token(email=email, purpose=purpose)
    await token.save()
    return await token.refresh()

@router.post(
    '/google/tts'
)
async def infer_google_tts(
    text: str = Form(...),
    language: str = Form('english'),
):
    audio = call_google_tts(text, language)
    return {'audio': audio, 'format': 'mp3'}

@router.post(
    '/external'
)
async def infer_external_commercial_ocr(
    image: UploadFile = File(...),
    language: str = Form(''),
    token: Token = Depends(get_token)
):
    tmp = TemporaryDirectory()
    location = join(tmp.name, '{}.{}'.format(
        str(uuid.uuid4()),
        image.filename.strip().split('.')[-1]
    ))
    with open(location, 'wb+') as f:
        shutil.copyfileobj(image.file, f)
    if token.quota < 1:
        raise HTTPException(
            status_code=403,
            detail='Token Expired. Please fetch a new token and try again'
        )
    else:
        await token.update(quota=token.quota-1)
    await Log.create(
        user_token=token.id,
        language=language,
        version='google',
        image_count=1,
    )
    return call_google_ocr(language, tmp.name)

@router.post(
    '/google/token',
    response_model=Token
)
async def fetch_google_token(
    email: str = Form(''),
    purpose: str = Form(''),
) -> Token:
    existing_tokens = await Token.filter(email=email)
    if existing_tokens:
        return existing_tokens[0]
    token = Token(email=email, purpose=purpose)
    await token.save()
    return await token.refresh()


@router.post(
    '/google'
)
async def infer_google_ocr(
    image: UploadFile = File(...),
    language: str = Form(''),
    token: Token = Depends(get_token)
):
    tmp = TemporaryDirectory()
    location = join(tmp.name, '{}.{}'.format(
        str(uuid.uuid4()),
        image.filename.strip().split('.')[-1]
    ))
    with open(location, 'wb+') as f:
        shutil.copyfileobj(image.file, f)
    if token.quota < 1:
        raise HTTPException(
            status_code=403,
            detail='Token Expired. Please fetch a new token and try again'
        )
    else:
        await token.update(quota=token.quota-1)
    await Log.create(
        user_token=token.id,
        language=language,
        version='google',
        image_count=1,
    )
    return call_google_ocr(language, tmp.name)


@router.post('/google/mt')
async def infer_google_mt(
    text: str,
    # source: str,
    target: str,
):
    print(text, target)
    translate_client = translate.Client()
    result = translate_client.translate(text, target_language=target)
    return {
        'text': result['translatedText'],
    }
