from subprocess import call

from fastapi import APIRouter, Request, UploadFile, File, Form, Depends, HTTPException
from tempfile import TemporaryDirectory
from os.path import join

import uuid
import shutil
from .helper import call_page_tesseract2, call_google_ocr
from .models import Token, Log
from .dependencies import get_token

router = APIRouter(
	prefix='/ocr',
	tags=['External OCR APIs'],
)


@router.post(
	'/tesseract',
)
def infer_ocr(
	image: UploadFile = File(...),
	language: str = Form('english'),
	bilingual: bool = Form(False),
):
	tmp = TemporaryDirectory()
	location = join(tmp.name, '{}.{}'.format(
		str(uuid.uuid4()),
		image.filename.strip().split('.')[-1]
	))
	with open(location, 'wb+') as f:
		shutil.copyfileobj(image.file, f)
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
	language: str = Form('en'),
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
	await Log.create(token)
	return call_google_ocr(language, tmp.name)