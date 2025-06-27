import base64
from pathlib import Path

from fastapi.testclient import TestClient

from server.app import app
from server.config import LANGUAGES
from server.helper import verify_model
from server.models import LanguageEnum, VersionEnum

client = TestClient(app)


def get_all_models() -> list[tuple[str, str, str]]:
    versions = [i.value for i in list(VersionEnum)]
    langs = [(i.value, LANGUAGES[i.value]) for i in list(LanguageEnum)]
    ret = []
    for version in versions:
        for modality in ('printed', 'handwritten', 'scenetext'):
            for lang in langs:
                try:
                    verify_model(lang[1], version, modality)
                    ret.append((version, modality, lang[0]))
                except:
                    pass
    return ret


def test_main():
    images_folder = Path('/home/ocr/website/tests/samples/images/printed/hindi')
    images = images_folder.glob('*.jpg')
    images = [base64.b64encode(i.read_bytes()).decode() for i in images]
    models = get_all_models()[900]
    response = client.post(
        '/ocr/infer',
        headers={
            'Content-Type': 'application/json',
        },
        json={
            'imageContent': images,
            'version': models[0],
            'modality': models[1],
            'language': models[2],
        }
    )
    print(response.text)
    assert response.status_code == 200
    # assert response.json() == {"msg": "Hello World"}