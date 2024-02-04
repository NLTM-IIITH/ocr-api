import base64
import imghdr
import json
import os
import shutil
from datetime import datetime
from os.path import join
from tempfile import TemporaryDirectory
from subprocess import call
from typing import List
from uuid import uuid4

import pytz
import requests
from fastapi import HTTPException
from PIL import Image
import re

from .models import *
from .config import *

def download_models_from_file(file_path, output_folder):
    call(f'wget -i {file_path} -P {output_folder}',shell=True)

async def save_logs(request, response):
	dt = datetime.now(pytz.timezone('Asia/Kolkata')).isoformat()
	ret = {
		'ip_addr': str(request.client.host),
		'timestamp': dt,
		'request': await request.json(),
		'response': response.dict(),
	}
	dt = dt.strip().split('+')[0]
	formatted_dt = re.sub(r'[^a-zA-Z0-9]', '_', dt)

	# Use the modified timestamp in the filename
	filename = join(LOGS_FOLDER,f'{formatted_dt}.json')

	with open(filename, 'w', encoding='utf-8') as f:
		json.dump(ret, f, indent=4)

def process_image_content(image_content: str, savename: str) -> None:
	"""
	input the base64 encoded image and saves the image inside the folder.
	savename is the name of the image to be saved as
	"""
	print('received image as base64')
	savefolder = IMAGE_FOLDER
	assert isinstance(image_content, str)
	with open(join(savefolder, savename), 'wb') as f:
		f.write(base64.b64decode(image_content))
	os.system('cp {} /home/ocr/ulca_images/{}.jpg'.format(
		join(savefolder, savename),
		str(uuid4())
	))


def process_image_url(image_url: str, savename: str) -> None:
	"""
	input the url of the image and download and saves the image inside the folder.
	savename is the name of the image to be saved as
	"""
	print('received image as URL')
	tmp = TemporaryDirectory(prefix='save_image')
	savefolder = IMAGE_FOLDER
	r = requests.get(image_url, stream=True)
	print(r.status_code)
	if r.status_code == 200:
		r.raw.decode_content = True
		img_path = join(tmp.name, 'image')
		with open(img_path, 'wb') as f:
			shutil.copyfileobj(r.raw, f)
		img = Image.open(img_path)
		if imghdr.what(img_path) == 'png':
			img = img.convert('RGB')
		img.save(join(savefolder, savename))
		print('downloaded the image:', image_url)
	else:
		raise Exception('status_code is not 200 while downloading the image from url')

def process_images(images: List[ImageFile]):
	"""
	processes all the images in the given list.
	it saves all the images in the /home/ocr/website/images folder and
	returns this absolute path.
	"""
	print('deleting all the previous data from the images folder')
	os.system(f'rm -rf {IMAGE_FOLDER}/*')
	for idx, image in enumerate(images):
		if image.imageContent is not None:
			try:
				process_image_content(image.imageContent, '{}.jpg'.format(idx))
			except:
				raise HTTPException(
					status_code=400,
					detail='Error while decodeing and saving the image #{}'.format(idx)
				)
		elif image.imageUri is not None:
			try:
				process_image_url(image.imageUri, '{}.jpg'.format(idx))
			except:
				raise HTTPException(
					status_code=400,
					detail='Error while downloading and saving the image #{}'.format(idx)
				)
		else:
			raise HTTPException(
				status_code=400,
				detail='image #{} doesnt contain either imageContent or imageUri'.format(
					idx
				)
			)

def process_config(config: OCRConfig):
	global LANGUAGES
	try:
		language_code = config.languages[0].sourceLanguage.value
		language = LANGUAGES[language_code]
		modality = config.modality.value
		dlevel = config.detectionLevel.value
	except Exception as e:
		print(e)
		raise HTTPException(
			status_code=400,
			detail='language code is either not present or invalid'
		)
	return (language_code, language, modality, dlevel)


def process_ocr_output(language_code: str,modality: str, image_folder: str) -> OCRResponse:
	"""
	process the ./images/out.json file and returns the ocr response.
	"""
	try:
		a = open(os.path.join(image_folder,'out.json'), 'r').read().strip()
		a = json.loads(a)
		a = a.split('\n')
		a = [Sentence(source=i,target=language_code) for i in a if len(i)>0]
		
	except Exception as e:
		print(e)
		raise HTTPException(
			status_code=500,
			detail='Error while parsing the ocr output'
		)
	try:
		response = OCRResponse(
			config=OCRConfig(
				modelId=None,
				detectionLevel='page',
				modality=modality,
				languages=[LanguagePair(
					sourceLanguageName=LANGUAGES[language_code],
					sourceLanguage=language_code,
					targetLanguage=None,
					targetLanguageName=None,
				)],
			),
			output=a.copy(),
		)
	except Exception as e:
		print(f'OCRResponse ERROR: {e}')

	return response