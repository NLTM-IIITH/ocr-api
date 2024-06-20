import base64
import imghdr
import json
import os
import shutil
from datetime import datetime
from os.path import join
from tempfile import TemporaryDirectory
from uuid import uuid4

import pytz
import requests
from fastapi import HTTPException
from PIL import Image

from .models import ImageFile, LanguagePair, OCRConfig, OCRResponse, Sentence

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

async def save_logs(request, response):
    dt = datetime.now(pytz.timezone('Asia/Kolkata')).isoformat()
    ret = {
        'ip_addr': str(request.client.host),
        'timestamp': dt,
        'request': await request.json(),
        'response': response.dict(),
    }
    dt = dt.strip().split('+')[0]
    with open('/home/ocr/ulca_logs/{}.json'.format(dt), 'w', encoding='utf-8') as f:
        json.dump(ret, f, indent=4)

def process_image_content(image_content: str, savename: str) -> None:
    """
    input the base64 encoded image and saves the image inside the folder.
    savename is the name of the image to be saved as
    """
    print('received image as base64')
    savefolder = '/home/ocr/website/images'
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
    savefolder = '/home/ocr/website/images'
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

def process_images(images: list[ImageFile]):
    """
    processes all the images in the given list.
    it saves all the images in the /home/ocr/website/images folder and
    returns this absolute path.
    """
    print('deleting all the previous data from the images folder')
    os.system('rm -rf /home/ocr/website/images/*')
    for idx, image in enumerate(images):
        if image.imageContent is not None:
            try:
                process_image_content(image.imageContent, '{}.jpg'.format(idx))
            except Exception:
                raise HTTPException(
                    status_code=400,
                    detail='Error while decodeing and saving the image #{}'.format(idx)
                )
        elif image.imageUri is not None:
            try:
                process_image_url(image.imageUri, '{}.jpg'.format(idx))
            except Exception:
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
    print(config)
    try:
        language_code = config.languages[0].sourceLanguage.value
        language = LANGUAGES[language_code]
        modality = config.modality.value
        if modality == 'print':
            modality = 'printed'
        dlevel = config.detectionLevel.value
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=400,
            detail='language code is either not present or invalid'
        )
    return (language_code, language, modality, dlevel)

def process_ocr_output(language_code: str, modality: str, dlevel: str) -> OCRResponse:
    """
    process the ./images/out.json file and returns the ocr response.
    """
    try:
        a = open('/home/ocr/website/images/out.json', 'r').read().strip()
        a = json.loads(a)
        a = [(i, a[i]) for i in a]
        print(a)
        if len(a)>1:
            a = sorted(a, key=lambda x:int(x[0].split('.')[0]))
        a = [Sentence(source=i[1]) for i in a]
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=500,
            detail='Error while parsing the ocr output'
        )
    return OCRResponse(
        config=OCRConfig(
            languages=[LanguagePair(
                sourceLanguage=language_code,
            )],
        ),
        output=a.copy(),
    )
