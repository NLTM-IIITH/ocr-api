from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ModalityEnum(str, Enum):
    printed = 'printed'
    handwritten = 'handwritten'
    scenetext = 'scenetext'

class LanguageEnum(str, Enum):
    en = 'en'  # english
    hi = 'hi'  # hindi
    mr = 'mr'  # marathi
    ta = 'ta'  # tamil
    te = 'te'  # telugu
    kn = 'kn'  # kannada
    gu = 'gu'  # gujarati
    pa = 'pa'  # punjabi
    bn = 'bn'  # bengali
    ml = 'ml'  # malayalam
    asa = 'asa'  # assamese
    ori = 'ori'  # oriya
    mni = 'mni'  # manipuri
    ur = 'ur'  # urdu

    # extra languages
    brx = 'brx' # Bodo
    doi = 'doi' # Dogri
    ks = 'ks' # Kashmiri
    kok = 'kok' # Konkani
    mai = 'mai' # Maithili
    ne = 'ne' # Nepali
    sa = 'sa' # Sanskrit
    sat = 'sat' # Santali
    sd = 'sd' # Sindhi


class LevelEnum(str, Enum):
    word = 'word'
    line = 'line'
    paragraph = 'paragraph'
    page = 'page'

class VersionEnum(str, Enum):
    v0 = 'v0'
    v2 = 'v2'
    v2_bilingual = 'v2_bilingual'
    v2_robust = 'v2_robust'
    v2_1_robust = 'v2.1_robust'
    v3 = 'v3'
    v3_post = 'v3_post'
    v3_robust = 'v3_robust'
    v3_1_robust = 'v3.1_robust'
    v3_bilingual = 'v3_bilingual'
    v3_1_bilingual = 'v3.1_bilingual'
    v4 = 'v4'
    v4_robust = 'v4_robust'
    v4_bilingual = 'v4_bilingual'
    v4_robustbilingual = 'v4_robustbilingual'
    v4_1 = 'v4.1'
    v4_1_robust = 'v4.1_robust'
    v4_1_bilingual = 'v4.1_bilingual'
    v4_1_robustbilingual = 'v4.1_robustbilingual'
    v4_2 = 'v4.2'
    v4_2_robust = 'v4.2_robust'
    v4_2_bilingual = 'v4.2_bilingual'
    v4_2_robustbilingual = 'v4.2_robustbilingual'
    v4_3u = 'v4.3u'
    v4_3u_robust = 'v4.3u_robust'
    v4_3u_bilingual = 'v4.3u_bilingual'
    v4_3u_robustbilingual = 'v4.3u_robustbilingual'
    v4_4l = 'v4.4l'
    v4_4l_robust = 'v4.4l_robust'
    v4_4l_bilingual = 'v4.4l_bilingual'
    v4_4l_robustbilingual = 'v4.4l_robustbilingual'
    v4_5u = 'v4.5u'
    v4_5u_robust = 'v4.5u_robust'
    v4_5u_bilingual = 'v4.5u_bilingual'
    v4_5u_robustbilingual = 'v4.5u_robustbilingual'
    v1_iitb = 'v1_iitb'
    v4_6_robust = 'v4.6_robust'
    v4_7u = 'v4.7u'
    v4_7u_robust = 'v4.7u_robust'
    v4_8u = 'v4.8u'
    v4_8u_robust = 'v4.8u_robust'
    v4_9u = 'v4.9u'
    v4_9u_robust = 'v4.9u_robust'
    v4_10u = 'v4.10u'
    v4_10u_robust = 'v4.10u_robust'
    v4_11l = 'v4.11l'
    v4_11l_robust = 'v4.11l_robust'
    v4_11l_bilingual = 'v4.11l_bilingual'
    v4_11l_robustbilingual = 'v4.11l_robustbilingual'
    v4_12u = 'v4.12u'
    v4_13 = 'v4.13'
    v3_st = 'v3_st'
    v4_hw = 'v4_hw'
    v4_14u = 'v4.14u'
    v4_14u_robust = 'v4.14u_robust'
    v4_15a_robust = 'v4.15a_robust'
    v4_16a_robust = 'v4.16a_robust'
    v4_17a_robust = 'v4.17a_robust'
    v5 = 'v5'
    v5_robust = 'v5_robust'
    v5_bilingual = 'v5_bilingual'
    v5_robustbilingual = 'v5_robustbilingual'
    v5_robuster = 'v5_robuster'
    v5_robusterbilingual = 'v5_robusterbilingual'
    v5_urdu1 = 'v5_urdu1'
    v5_urdu2 = 'v5_urdu2'
    v5_urdu3 = 'v5_urdu3'
    v5_urdur1 = 'v5_urdur1'
    v5_urdur2 = 'v5_urdur2'

    # First V5 Upnishad Finetune
    v5_1_1u = 'v5.1.1u'
    v5_1_2u = 'v5.1.2u'
    v5_1_3u = 'v5.1.3u'
    v5_1_1u_robust = 'v5.1.1u_robust'
    v5_1_2u_robust = 'v5.1.2u_robust'
    v5_1_1u_bilingual = 'v5.1.1u_bilingual'
    v5_1_2u_bilingual = 'v5.1.2u_bilingual'
    v5_1_3u_bilingual = 'v5.1.3u_bilingual'
    v5_1_1u_robustbilingual = 'v5.1.1u_robustbilingual'
    v5_1_2u_robustbilingual = 'v5.1.2u_robustbilingual'

    v4_15_m = 'v4.15m'

    v6 = 'V-01.06.00.00'
    v4_18 = 'V-01.04.00.18'
    v4_robust_18 = 'V-01.04.01.18'
    v4_19 = 'V-01.04.00.19'
    v4_robust_19 = 'V-01.04.01.19'

    parliament = 'parliament'
    parliamentr = 'parliamentr'

    lipikar = 'lipikar'
    v1_pu = 'v1_pu'
    v2_iitb = 'v2_iitb'
    v3_iitb = 'v3_iitb'

    tesseract = 'tesseract'
    tesseract_pad = 'tesseract_pad'
    v1_st_iitj = 'v1_st_iitj'
    tesseract_bi = 'tesseract_bi'

    v01040021 = 'V-01.04.00.21'


class OCRRequest(BaseModel):
    imageContent: List[str]
    modality: Optional[ModalityEnum] = Field(
        ModalityEnum.printed,
        description='Describes the modality of the model to be called'
    )
    level: Optional[LevelEnum] = Field(
        LevelEnum.word,
        description='Describes the detection level of the model to be called'
    )
    language: LanguageEnum
    version: Optional[VersionEnum] = Field(
        VersionEnum.v2,
        description='Describes the version no of the models to be called (IIITH)'
    )
    modelid: Optional[str] = Field(
        '',
        description='Describes the ID/Key of the model to be called'
    )
    omit: Optional[bool] = Field(
        True,
        description='Specifies whether to omit the meta details from the OCRResponse'
    )
    meta: Optional[Dict[Any, Any]] = Field(
        {},
        description='Extra meta details to give to the model'
    )


class OCRImageResponse(BaseModel):
    """
    This is the model placeholder for the ocr output of a single image
    """
    text: str
    meta: Optional[Dict[Any, Any]] = Field(
        {},
        description='Meta information given by model for each image'
    )


class PostprocessRequest(BaseModel):
    language: LanguageEnum
    vocabulary: List[str]
    lexicon: Optional[List[str]] = []
    words: List[OCRImageResponse]


class PostprocessImageResponse(BaseModel):
    text: List[str]
    meta: Optional[Dict[Any, Any]] = Field(
        {},
        description='Meta information given by model for each image'
    )
