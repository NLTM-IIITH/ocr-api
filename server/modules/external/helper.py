import base64
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
from PIL import Image

import pytesseract
from server.config import LANGUAGES, NUMBER_LOADED_MODEL_THRESHOLD, TESS_LANG

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
