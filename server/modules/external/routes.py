from subprocess import call

from fastapi import APIRouter, Request, UploadFile, File, Form
from tempfile import TemporaryDirectory
from os.path import join

import uuid
import shutil
from .helper import call_page_tesseract2

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