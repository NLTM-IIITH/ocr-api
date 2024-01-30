import base64
import cv2
import imghdr
import json
import os
import shutil
from datetime import datetime
from os.path import join
from tempfile import TemporaryDirectory
from typing import List
from uuid import uuid4

import pytz
import requests
from fastapi import HTTPException
from fastapi.responses import FileResponse
from PIL import Image

import pytesseract
from server.config import LANGUAGES, NUMBER_LOADED_MODEL_THRESHOLD, TESS_LANG
from google.cloud import vision

from .models import *

# This is the reference to convert language codes to language name
LANGUAGES = {
	'hi': 'hindi',
	'mr': 'marathi',
	'ta': 'tamil',
	'te': 'telugu',
	'kn': 'kannada',
	'gu': 'gujarati',
	'pa': 'punjabi',
	'bn': 'bengali',
	'ml': 'malayalam',
	'as': 'assamese',
	'mni': 'manipuri',
	'or': 'oriya',
	'ur': 'urdu',
}

def call_page_tesseract2(language, folder, bilingual: bool = False):
	a = [join(folder, i) for i in os.listdir(folder)]
	if bilingual:
		ret = pytesseract.image_to_string(a[0], lang='eng+'+TESS_LANG[language]).strip()
	else:
		ret = pytesseract.image_to_string(a[0], lang=TESS_LANG[language]).strip()
	return {'text': ret}

def parse_google_response(response):
	a = response.full_text_annotation
	ret = {
		'text': a.text.strip()
	}
	words = []
	for page in a.pages:
		for block in page.blocks:
			for paragraph in block.paragraphs:
				for word in paragraph.words:
					t = ''
					for symbol in word.symbols:
						t += str(symbol.text)
					print(t)
					words.append({
						'text': t.strip(),
						'bounding_box': {
							'x': word.bounding_box.vertices[0].x,
							'y': word.bounding_box.vertices[0].y,
							'w': word.bounding_box.vertices[2].x - word.bounding_box.vertices[0].x,
							'h': word.bounding_box.vertices[2].y - word.bounding_box.vertices[0].y,
						}
					})
	ret['meta'] = {'words': words}
	return ret

def visualize_google(image_path, response):
	words = parse_google_response(response)
	img = cv2.imread(image_path)
	for i in words:
		img = cv2.rectangle(
			img,
			(i['bounding_box']['x'], i['bounding_box']['y']),
			(i['bounding_box']['x']+i['bounding_box']['w'], i['bounding_box']['y']+i['bounding_box']['h']),
			(0,0,255),
			3
		)
		img = cv2.putText(
			img,
			i['text'],
			(i['bounding_box']['x']-5, i['bounding_box']['y']-5),
			cv2.FONT_HERSHEY_COMPLEX,
			1,
			(0,0,255),
			1,
			cv2.LINE_AA
		)
	save_location = '/home/ocr/visualizations/test.jpg'
	cv2.imwrite(save_location, img)
	return FileResponse(save_location)

def call_google_ocr(language, folder):
	a = [join(folder, i) for i in os.listdir(folder)]
	ret = []
	client = vision.ImageAnnotatorClient()
	for i in a:
		with open(i, 'rb') as f:
			img = vision.Image(content=f.read())
		response = client.document_text_detection(
			image=img,
			image_context={
				'language_hints': [language]
			}
		)
		ret.append(parse_google_response(response))
	return ret