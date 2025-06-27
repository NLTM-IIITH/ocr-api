import base64
import io
import json
import multiprocessing
import os
import time
from os.path import basename, join
from subprocess import call

import cv2
import pytesseract
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import \
    OperationStatusCodes
from fastapi import HTTPException
from fastapi.responses import FileResponse
from google.cloud import texttospeech, vision
from msrest.authentication import CognitiveServicesCredentials
from pydub import AudioSegment

from server.config import EASYOCR_LANG, SURYA_LANG, TESS_LANG

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

def call_page_easyocr(language, folder):
    if language not in EASYOCR_LANG:
        raise HTTPException(
            status_code=400,
            detail=f'EasyOCR model not available for {language}'
        )
    call(
        f'./infer_easyocr.sh {EASYOCR_LANG[language]} {folder}',
        shell=True
    )
    with open(join(folder, 'out.json'), 'r', encoding='utf-8') as f:
        return json.loads(f.read().strip())

def call_page_azure(image_path):
    subscription_key = os.environ['VISION_KEY']
    endpoint = os.environ['VISION_ENDPOINT']
    computervision_client = ComputerVisionClient(endpoint, CognitiveServicesCredentials(subscription_key))
    with open(image_path, 'rb') as f:
        read_response = computervision_client.read_in_stream(f, raw=True)
    read_operation_location = read_response.headers['Operation-Location']
    operation_id = read_operation_location.split('/')[-1]

    while True:
        read_result = computervision_client.get_read_result(operation_id)
        if read_result.status not in ('notStarted', 'running'):
            break
        time.sleep(1)
    text = []
    words = []
    lineno = 0
    if read_result.status == OperationStatusCodes.succeeded:
        for text_result in read_result.analyze_result.read_results:
            for line in text_result.lines:
                lineno += 1
                text.append(line.text.strip())
                for word in line.words:
                    bbox = list(map(int, word.bounding_box))
                    x = [
                        bbox[0], bbox[2],
                        bbox[4], bbox[6],
                    ]
                    y = [
                        bbox[1], bbox[3],
                        bbox[5], bbox[7],
                    ]
                    words.append({
                        'bounding_box': {
                            'x': min(x),
                            'y': min(y),
                            'w': max(x) - min(x),
                            'h': max(y) - min(y),
                        },
                        'line': lineno,
                        'label': word.text.strip(),
                    })
    else:
        raise HTTPException(
            status_code=500,
            detail='Azure Read result not succedded'
        )
    return {
        'text': '\n'.join(text),
        'words': words
    }

def call_page_surya(language, folder):
    if language not in SURYA_LANG:
        raise HTTPException(
            status_code=400,
            detail=f'Surya model not available for {language}'
        )
    call(
        f'./infer_surya.sh {SURYA_LANG[language]} {folder}',
        shell=True
    )
    with open(join(folder, 'out.json'), 'r', encoding='utf-8') as f:
        return json.loads(f.read().strip())


def call_single_tess(image_info):
    image_path, language, bilingual = image_info
    print(f'Processing file: {basename(image_path)}')
    if bilingual:
        out = pytesseract.image_to_string(image_path, lang='eng'+TESS_LANG[language]).strip()
    else:
        out = pytesseract.image_to_string(image_path, lang=TESS_LANG[language]).strip()
    return {'text': out, 'regions': []}

def call_page_tesseract2(language, folder, bilingual: bool = False):
    images = [join(folder, i) for i in os.listdir(folder)]
    infos = [(i, language, bilingual) for i in images]
    with multiprocessing.Pool(processes=5) as pool:
        ret = pool.map(call_single_tess, infos)
    return ret


def call_page_tesseract_unbulk(language, folder, bilingual: bool = False):
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
                    x = {
                        'text': t.strip(),
                        'bounding_box': {
                            'x': word.bounding_box.vertices[0].x,
                            'y': word.bounding_box.vertices[0].y,
                            'w': word.bounding_box.vertices[2].x - word.bounding_box.vertices[0].x,
                            'h': word.bounding_box.vertices[2].y - word.bounding_box.vertices[0].y,
                        },
                    }
                    try:
                        x.update({
                            'confidence': round(float(word.confidence), 2),
                            'language_code': str(word.property.detected_languages[0].language_code),
                        })
                    except Exception:
                        pass
                    words.append(x)
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
        tic1 = time.time()

        with open(i, 'rb') as f:
            img = vision.Image(content=f.read())

        tic1 = round(float(time.time() - tic1), 2)
        tic2 = time.time()

        response = client.document_text_detection(
            image=img,
            image_context={
                'language_hints': [language]
            } if language else {}
        )

        tic2 = round(float(time.time() - tic2), 2)
        tic3 = time.time()

        ret.append(parse_google_response(response))

        tic3 = round(float(time.time() - tic3), 2)

        print(f'[{tic1}s / {tic2}s / {tic3}s] Time takes to load image, call google ocr, and parse the response')
    return ret


def preprocess_tts_text(text: str) -> list[str]:
    if len(text.encode()) < 4900:
        print(f'Audio length {len(text.encode())}; No need to trim.')
        return [text]
    words = text.split(' ')
    ret = []
    t = []
    charlen = 0
    for i in words:
        if charlen > 4000:
            ret.append(' '.join(t))
            t, charlen = [], 0
        t.append(i)
        charlen += len(i.encode())
    print(f'Audio length {len(text.encode())}; Trimming into {len(ret)} smaller sections')
    return ret

def call_single_google_tts(text: str, language: str = 'english'):
    lang_map = {
        'bengali': 'bn-In',
        'english': 'en-IN',
        'gujarati': 'gu-IN',
        'hindi': 'hi-IN',
        'kannada': 'kn-IN',
        'malayalam': 'ml-IN',
        'marathi': 'mr-IN',
        'punjabi': 'pa-IN',
        'tamil': 'ta-IN',
        'telugu': 'te-IN',
    }
    lang = lang_map.get(language, 'en-IN')
    print(lang)
    client = texttospeech.TextToSpeechClient()
    inp = texttospeech.SynthesisInput(text=text)
    if lang[:2] in ('en', 'hi', 'mr'):
        name = 'Chirp3-HD-Aoede'
    else:
        name = 'Wavenet-A'
    voice = texttospeech.VoiceSelectionParams(
        language_code=lang,
        # name=f'{lang}-Wavenet-A',
        name=f'{lang}-{name}',
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
    response = client.synthesize_speech(
        input=inp,
        voice=voice,
        audio_config=audio_config
    )
    return base64.b64encode(response.audio_content).decode()

def merge_base64_audio(audio_list: list[str]):
    audio = AudioSegment.empty()
    for i in audio_list:
        audio += AudioSegment.from_file(
            io.BytesIO(base64.b64decode(i)),
            format='mp3'
        )
    output_io = io.BytesIO()
    audio.export(output_io, format='mp3')
    return base64.b64encode(output_io.getvalue()).decode()

def call_google_tts(text: str, language: str = 'english'):
    text_list = preprocess_tts_text(text)
    audio_list = []
    for i in text_list:
        audio_list.append(call_single_google_tts(i, language))
    # audio_list = list(map(call_single_google_tts, text_list))
    return merge_base64_audio(audio_list)