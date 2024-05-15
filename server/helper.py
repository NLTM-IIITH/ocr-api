import base64
import tempfile
import asyncio
import random
from PIL import Image
from tqdm import tqdm
import subprocess
import json
import os
from os.path import basename, join, splitext
from subprocess import call, check_output
from typing import List, Tuple

import pytesseract
from fastapi import HTTPException

from server.config import LANGUAGES, NUMBER_LOADED_MODEL_THRESHOLD, TESS_LANG

from .models import *


def check_loaded_model() -> List[Tuple[str, str, str]]:
	"""
	This function run the docker container ls on the host and checks
	if any docker container is already running for ocr.
	if running then it returns the language of the container
	"""
	command = 'docker container ls --format "{{.Names}}"'

	a = check_output(command, shell=True).decode('utf-8').strip().split('\n')
	a = [i.strip() for i in a if i.strip().startswith('infer')]  

	return [tuple(i.split('-')[1:]) for i in a]


def load_model(modality: str, language: str, modelid: str) -> None:
	"""
	This function calls the load_v0.sh bash file to start the
	model flask server.
	"""
	loaded_model = check_loaded_model()
	if tuple([modality, language, modelid]) not in loaded_model:
		if (len(loaded_model) >= NUMBER_LOADED_MODEL_THRESHOLD):
			print('unloading the oldest model')
			call('./unload_oldest.sh', shell=True)
		print('loading the new model')
		call(
			f'./load.sh {modality} {language} {modelid} /home/ocr/website/images',
			shell=True
		)
	else:
		print('model already loaded. No need to reload')



def process_images(images: List[str], save_path) -> int:
	"""
	processes all the images in the given list.
	it saves all the images in the save_path folder.
	"""
	for idx, image in enumerate(images):
		try:
			with open(join(save_path, f'{idx}.jpg'), 'wb') as f:
				f.write(base64.b64decode(image))
		except:
			raise HTTPException(
				status_code=400,
				detail=f'Error while decoding and saving the image #{idx}',
			)
	return len(images)


def process_language(lcode: LanguageEnum) -> Tuple[str, str]:
	return (lcode.value, LANGUAGES[lcode.value])

def process_modality(modal_type: ModalityEnum) -> str:
	return modal_type.value

def process_version(ver_no: VersionEnum) -> str:
	return ver_no.value


def verify_model(language, version, modality):
	"""
	function that raises httpexception if the model is not available.
	"""
	minor_languages = [
		'bodo',
		'dogri',
		'kashmiri',
		'konkani',
		'maithili',
		'nepali',
		'sanskrit',
		'santali',
		'sindhi',
	]
	try:
		# support for minor languages
		if language in minor_languages:
			assert version in ('v4_robust', 'v4.15m')
		elif version == 'v2':
			assert language != 'english'
		elif version == 'v2_robust':
			assert modality == 'printed'
		elif version == 'v2.1_robust':
			# upnishad fine-tuned robust model
			assert modality  == 'printed' and language == 'telugu'
		elif version == 'v2_bilingual':
			assert modality == 'printed' and language not in [
				'english',
				'hindi',
				'urdu'
			]
		elif version == 'v3':
			assert modality == 'handwritten'
		elif version == 'v3_post':
			assert modality == 'handwritten'
		elif version == 'v3_robust':
			assert modality == 'printed' and language not in [
				'assamese',
				'hindi',
				'urdu'
			]
		elif version == 'v3.1_robust':
			assert modality == 'printed' and language == 'telugu'
		elif version == 'v3_bilingual':
			assert modality  == 'printed' and language == 'telugu'
		elif version == 'v3.1_bilingual':
			assert modality  == 'printed' and language == 'telugu'
		elif version in ['v4', 'v4_robust']:
			assert modality == 'printed' and language != 'urdu'
		elif version in ['v4_bilingual', 'v4_robustbilingual']:
			assert modality == 'printed' and language not in ['english', 'urdu']
		elif any((
			version.startswith('v4.4'),
			version.startswith('v4.11'),
			version.startswith('v4.15'),
			version.startswith('v4.16'),
			version.startswith('v4.17'),
		)):
			assert modality == 'printed' and language == 'hindi'
		elif any((
			version.startswith('v4.13'),
		)):
			assert modality == 'printed' and language == 'english'
		elif any((
			version.startswith('v4.1'),
			version.startswith('v4.2'),
			version.startswith('v4.3'),
			version.startswith('v4.5'),
			version.startswith('v4.7'),
			version.startswith('v4.8'),
			version.startswith('v4.9'),
			version.startswith('v4.10'),
			version.startswith('v4.12'),
			version.startswith('v4.14'),
		)):
			assert modality == 'printed' and language == 'telugu'
		elif any((
			version.startswith('v4.6'),
		)):
			assert modality == 'printed' and language == 'bengali'
		elif version == 'v1_iitb':
			assert modality == 'handwritten' and language not in [
				'assamese',
				'kannada',
				'malayalam',
				'manipuri',
				'marathi'
			] or modality == 'printed' and language in [
				'hindi',
				'kannada',
				'marathi',
				'tamil',
				'telugu',
			]
		elif version == 'tesseract':
			assert modality == 'printed' and language != 'manipuri'
		elif version == 'v3_st':
			assert modality == 'scenetext' and language != 'english'
		elif version == 'v4_hw':
			assert modality == 'handwritten' and language not in [
				'assamese',
				'english',
				'manipuri',
				'marathi',
			]
		elif version == 'v1_st_iitj':
			assert modality == 'scenetext' and language not in [
					'hindi',
					'english',
					'assamese',
					'malayalam',
					'punjabi',
					'tamil',
			]
		elif version == 'V-01.06.00.00':
			assert modality == 'handwritten' and language != 'english'
		elif version in ('parliament', 'parliamentr'):
			assert modality == 'printed' and language == 'hindi'
		elif version in ('V-01.04.00.18', 'V-01.04.01.18'):
			assert modality == 'printed' and language in ('english', 'hindi')
		elif version in ('V-01.04.00.19', 'V-01.04.01.19'):
			assert modality == 'printed' and language in ('english', 'hindi')
	except AssertionError:
		raise HTTPException(
			status_code=400,
			detail=f'No model available for {language} {version} {modality}'
		)
	except Exception as e:
		print(e)
		raise HTTPException(
			status_code=500,
			detail='Unknown exception while verifing the models'
		)


def process_ocr_output(image_folder: str) -> List[OCRImageResponse]:
	"""
	process the <folder>/out.json file and returns the ocr response.
	"""
	sorting_func = lambda x:int(x[0].split('.')[0])
	try:
		with open(join(image_folder, 'out.json'), 'r', encoding='utf-8') as f:
			a = f.read().strip()
		a = json.loads(a)
		a = list(a.items())
		a = sorted(a, key=sorting_func)
		prob_path = join(image_folder, 'prob.json')
		if os.path.exists(prob_path):
			with open(prob_path, 'r', encoding='utf-8') as f:
				probs = f.read().strip()
			probs = json.loads(probs)
			return [OCRImageResponse(text=i[1], meta=probs[i[0]]) for i in a]
		return [OCRImageResponse(text=i[1]) for i in a]
	except Exception as e:
		print(e)
		raise HTTPException(
			status_code=500,
			detail='Error while parsing the ocr output'
		)


def add_padding(images, size: int):
	for image in tqdm(images, desc='Adding Padding'):
		img = Image.open(image)
		w,h = img.size
		out = Image.new(img.mode, (w+size*2, h+size*2), (255,255,255))
		out.paste(img, (size, size))
		out.save(image)

async def call_page_pu(language, folder):
	a = [join(folder, i) for i in os.listdir(folder)]
	b = os.getcwd()
	code_path = '/home/ocr/models/code/v1_pu/{}'.format(language)
	command = [
		'/home/ocr/temp_venv/bin/python',
		f'{code_path}/main.py',
		a[0]
	]
	process = await asyncio.create_subprocess_exec(*command, cwd=code_path)
	await process.wait()
	os.chdir(b)
	with open('{}/output.txt'.format(code_path), 'r', encoding='utf-8') as f:
		ret = f.read().strip()
	return [
		OCRImageResponse(text=ret, meta={})
	]

def call_page_tesseract(language, folder):
	a = [join(folder, i) for i in os.listdir(folder)]
	try:
		a.sort(key=lambda x:int(splitext(basename(x))[0]))
	except:
		a.sort()
	lang = TESS_LANG[language]
	ret = []
	for i in tqdm(a, desc='processing tesseract'):
		x = pytesseract.image_to_string(i, lang=lang).strip()
		ret.append(
			OCRImageResponse(
				text=x,
				meta={}
			)
		)
	return ret

def call_page_tesseract_pad(language, folder):
	tmp = tempfile.TemporaryDirectory()
	a = []
	for i in tqdm(os.listdir(folder), desc='Padding images'):
		location = join(tmp.name, i)
		img = Image.open(join(folder, i))
		new_img = Image.new('RGB', (2480,3508), (255,255,255))
		new_img.paste(img, (100, 100))
		new_img.convert('RGB').save(location)
		a.append(location)
	try:
		a.sort(key=lambda x:int(splitext(basename(x))[0]))
	except:
		a.sort()
	lang = TESS_LANG[language]
	ret = []
	for i in tqdm(a, desc='processing tesseract'):
		x = pytesseract.image_to_string(i, lang=lang).strip()
		ret.append(
			OCRImageResponse(
				text=x,
				meta={}
			)
		)
	return ret