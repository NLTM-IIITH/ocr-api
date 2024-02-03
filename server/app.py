import os
import shutil
import time
from dataclasses import dataclass
import uuid
from datetime import datetime
from os.path import join
from subprocess import call
from tempfile import TemporaryDirectory
from typing import List

from dateutil.tz import gettz
from fastapi import Depends, FastAPI, Form, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from .dependencies import save_uploaded_images
from .helper import *
from .models import OCRImageResponse, OCRRequest, PostprocessRequest
from .modules.cegis.routes import router as cegis_router
from .modules.ulca.routes import router as ulca_router
from .modules.external.routes import router as external_router
from .modules.iitb_v2.routes import router as iitb_v2_router
from server.config import IMAGE_FOLDER

from .database import close_mongo_connection, connect_to_mongo

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



@app.middleware('http')
async def log_request_timestamp(request: Request, call_next):
	local_tz = gettz('Asia/Kolkata')
	print(f'Received request at: {datetime.now(tz=local_tz).isoformat()}')
	return await call_next(request)


@app.get('/ocr/ping', tags=['Testing'])
def test_server_online():
	return 'pong'


# @dataclass
# class CustomDir:
# 	name: str


def save_uploaded_image(image: UploadFile) -> str:
	"""
	function to save the uploaded image to the disk

	@returns the absolute location of the saved image
	"""
	t = time.time()
	print('removing all the previous uploaded files from the image folder')
	os.system(f'rm -rf {IMAGE_FOLDER}/*')
	location = join(IMAGE_FOLDER, '{}.{}'.format(
		str(uuid.uuid4()),
		image.filename.strip().split('.')[-1]
	))
	with open(location, 'wb+') as f:
		shutil.copyfileobj(image.file, f)
	return location


# @app.post(
# 	'/ocr/tesseract',
# 	tags=['OCR'],
# )
# def infer_ocr(
# 	image: UploadFile = File(...),
# 	language: str = Form('english'),
# 	bilingual: bool = Form(False),
# ):
# 	tmp = TemporaryDirectory(prefix='hh')
# 	location = join(tmp.name, '{}.{}'.format(
# 		str(uuid.uuid4()),
# 		image.filename.strip().split('.')[-1]
# 	))
# 	with open(location, 'wb+') as f:
# 		shutil.copyfileobj(image.file, f)
# 	return call_page_tesseract2(language, tmp.name, bilingual)

@app.post(
	'/ocr/infer',
	tags=['OCR'],
	response_model=List[OCRImageResponse],
	response_model_exclude_none=True
)
def infer_ocr(ocr_request: OCRRequest) -> List[OCRImageResponse]:
	tmp = TemporaryDirectory(prefix='ocr_images')
	# tmp = CustomDir(name='/home/ocr/test')
	process_images(ocr_request.imageContent, tmp.name)

	lcode, language = process_language(ocr_request.language)
	version = process_version(ocr_request.version)
	modality = process_modality(ocr_request.modality)
	print('before verification', language, version, modality)
	verify_model(language, version, modality)
	if 'bilingual' in version:
		language = f'english_{language}'
	print(language, version, modality)
	if version == 'v0':
		load_model(modality, language, version)
		call(f'./infer_v0.sh {modality} {language}', shell=True)
	elif version == 'v1_iitb':
		call(f'./infer_v1_iitb.sh {modality} {language} {tmp.name}', shell=True)
	elif version == 'v2_iitb':
		call(f'./infer_v2_iitb.sh {modality} {lcode} {tmp.name}', shell=True)
	elif version == 'v1_pu':
		return call_page_pu(language, tmp.name)
	elif version == 'tesseract':
		folder = tmp.name
		return call_page_tesseract(language, folder)
	elif version == 'tesseract_bi':
		folder = tmp.name
		return call_page_tesseract_bi(language, folder)
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
	return process_ocr_output(tmp.name)


@app.post(
	'/ocr/test',
	tags=['Test OCR'],
	response_model=List[OCRImageResponse],
	response_model_exclude_none=True
)
def infer_ocr(
	images: List[UploadFile] = Depends(save_uploaded_images),
	language: LanguageEnum = Form(LanguageEnum.hi),
	modality: ModalityEnum = Form(ModalityEnum.printed),
	version: VersionEnum = Form(VersionEnum.v2),
) -> List[OCRImageResponse]:
	print(images)
	_, language = process_language(language)
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
	elif version == 'tesseract':
		# call_tesseract(language, folder)
		return call_page_tesseract(language, folder)
	else:
		call(
			f'./infer.sh {modality} {language} {folder} {version}',
			shell=True
		)
	return process_ocr_output(folder)
	# if version == 'v0':
	# 	load_model(modality, language, version)
	# 	call(f'./infer_v0.sh {modality} {language}', shell=True)
	# elif version == 'v1_iitb':
	# 	call(f'./infer_v1_iitb.sh {modality} {language} /home/ocr/website/images', shell=True)
	# else:
	# 	call(
	# 		f'./infer.sh {modality} {language} /home/ocr/website/images {version}',
	# 		shell=True
	# 	)
	# return process_ocr_output('/home/ocr/website/images')


@app.post(
	'/ocr/newpostprocess',
	tags=['OCR'],
	response_model=List[PostprocessImageResponse],
	response_model_exclude_none=True,
)
def OCR_newpostprocess(request: PostprocessRequest) -> List[PostprocessImageResponse]:
	"""
	This is the endpoint to postprocess the OCR output.
	This endpoints takes the same input as OCRResponse and outputs
	a list of acceptable alternatives for each word in the output.
	"""
	tmp = TemporaryDirectory(prefix='postprocess')
	# main_folder = tmp.name
	main_folder = '/home/ocr/temp'
	os.system(f'rm -rf {main_folder}/*')
	data_prob_folder = join(main_folder, 'data_prob')
	max_prob_folder = join(main_folder, 'max_prob')
	os.system(f'mkdir {data_prob_folder}')
	os.system(f'mkdir {max_prob_folder}')
	vocab_path = join(main_folder, 'vocabulary.txt')
	ocr_path = join(main_folder, 'ocr_output.txt')
	lexicon_path = join(main_folder, 'lexicon.txt')
	with open(vocab_path, 'w', encoding='utf-8') as f:
		f.write('\n'.join(request.vocabulary))
	with open(lexicon_path, 'w', encoding='utf-8') as f:
		f.write('\n'.join(request.lexicon))
	ocr_output = []
	for i,v in enumerate(request.words):
		print(f'processing for -> {i+1}')
		ocr_output.append(f'{i+1}.jpg\t{v.text}')
		with open(join(data_prob_folder, f'{i+1}.pts'), 'wb') as f:
			f.write(base64.b64decode(v.meta['data_prob']))
		with open(join(max_prob_folder, f'{i+1}.pts'), 'wb') as f:
			f.write(base64.b64decode(v.meta['max_prob']))
	with open(ocr_path, 'w', encoding='utf-8') as f:
		f.write('\n'.join(ocr_output))

	call(f'./infer_newpostprocess.sh {main_folder}', shell=True)
	a = open(join(main_folder, 'out.txt'), 'r', encoding='utf-8').read().strip().split('\n')
	ret = []
	for i in a:
		x = i.strip().split(' ')
		x = [j.strip() for j in x]
		x = list(set(x[1:]))
		ret.append(
			PostprocessImageResponse(text=x)
		)
	return ret


@app.post(
	'/ocr/postprocess',
	tags=['OCR'],
	response_model=List[PostprocessImageResponse],
	response_model_exclude_none=True,
)
def OCR_postprocess(request: PostprocessRequest) -> List[PostprocessImageResponse]:
	"""
	This is the endpoint to postprocess the OCR output.
	This endpoints takes the same input as OCRResponse and outputs
	a list of acceptable alternatives for each word in the output.
	"""
	tmp = TemporaryDirectory(prefix='postprocess')
	# main_folder = tmp.name
	main_folder = '/home/ocr/temp'
	os.system(f'rm -rf {main_folder}/*')
	data_prob_folder = join(main_folder, 'data_prob')
	max_prob_folder = join(main_folder, 'max_prob')
	os.system(f'mkdir {data_prob_folder}')
	os.system(f'mkdir {max_prob_folder}')
	vocab_path = join(main_folder, 'vocabulary.txt')
	ocr_path = join(main_folder, 'ocr_output.txt')
	with open(vocab_path, 'w', encoding='utf-8') as f:
		f.write('\n'.join(request.vocabulary))
	ocr_output = []
	for i,v in enumerate(request.words):
		print(f'processing for -> {i+1}')
		ocr_output.append(f'{i+1}.jpg\t{v.text}')
		with open(join(data_prob_folder, f'{i+1}.pts'), 'wb') as f:
			f.write(base64.b64decode(v.meta['data_prob']))
		with open(join(max_prob_folder, f'{i+1}.pts'), 'wb') as f:
			f.write(base64.b64decode(v.meta['max_prob']))
	with open(ocr_path, 'w', encoding='utf-8') as f:
		f.write('\n'.join(ocr_output))

	_, language = process_language(request.language)
	call(f'./infer_postprocess.sh {language} {main_folder}', shell=True)
	a = open(join(main_folder, 'out.txt'), 'r', encoding='utf-8').read().strip().split('\n')
	ret = []
	for i in a:
		x = i.strip().split(' ')
		x = [j.strip() for j in x]
		x = list(set(x[1:]))
		ret.append(
			PostprocessImageResponse(text=x)
		)
	return ret

