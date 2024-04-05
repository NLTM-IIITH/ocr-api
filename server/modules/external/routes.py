from subprocess import call
from PIL import Image
import io

from fastapi import APIRouter, Request, UploadFile, File, Form, Depends, HTTPException
from tempfile import TemporaryDirectory
from os.path import join

import uuid
import shutil
from .helper import call_page_tesseract2, call_google_ocr
from .models import Token
from ..core.models import Log
from .dependencies import get_token

router = APIRouter(
	prefix='/ocr',
	tags=['External OCR APIs'],
)


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
	return call_page_tesseract2(language, tmp.name, bilingual)


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
			status_code=400,
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