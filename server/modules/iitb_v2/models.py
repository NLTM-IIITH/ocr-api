from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class LevelEnum(str, Enum):
	word = 'word'
	char = 'char'

class ModalityEnum(str, Enum):
	printed = 'printed'
	handwritten = 'handwritten'
	scenetext = 'scenetext'

class LanguageEnum(str, Enum):
	en = 'en'	# english
	hi = 'hi'	# hindi
	mr = 'mr'	# marathi
	ta = 'ta'	# tamil
	te = 'te'	# telugu
	kn = 'kn'	# kannada
	gu = 'gu'	# gujarati
	pa = 'pa'	# punjabi
	bn = 'bn'	# bengali
	ml = 'ml'	# malayalam
	asa = 'as'	# assamese
	ori = 'or'	# oriya
	mni = 'mni'	# manipuri
	ur = 'ur'	# urdu

class DetectionLevelEnum(str, Enum):
	word = 'word'
	line = 'line'
	paragraph = 'paragraph'
	page = 'page'

class LanguagePair(BaseModel):
	"""
	description: language pair, make targetLanguage null to reuse the
	object to indicate single language
	"""
	sourceLanguageName: Optional[str] = Field(
		description='human name associated with the language code',
	)
	sourceLanguage: LanguageEnum = Field(
		description='Indic language code, iso-639-1, iso 639-2',
	)
	targetLanguage: Optional[LanguageEnum] = Field(
		description='Indic language code, iso-639-1, iso 639-2',
	)
	targetLanguageName: Optional[str] = Field(
		description='human name associated with the language code',
	)

class OCRConfig(BaseModel):
	modelId: Optional[str] = Field(
		description='Unique identifier of model',
	)
	detectionLevel: Optional[DetectionLevelEnum] = Field(
		DetectionLevelEnum.word,
		description=''
	)
	modality: Optional[ModalityEnum] = Field(
		ModalityEnum.printed,
		description=''
	)
	languages: List[LanguagePair]

class ImageFile(BaseModel):
	imageContent: Optional[str] = Field(
		description='image content',
	)
	imageUri: Optional[str] = Field(
		description='path on gcp/s3 bucket or https url',
	)

class OCRRequest(BaseModel):
	image: List[ImageFile]
	config: OCRConfig


class Sentence(BaseModel):
	source: str = Field(
		description='input sentence for the model',
	)
	target: Optional[str] = Field(
		description='to be used along with translation model. expected translated sentence, for reference',
	)


class OCRResponse(BaseModel):
	"""
	description: the response for translation. Standard http status codes to be used.
	"""
	output: List[Sentence]
	config: Optional[OCRConfig]


class OCRIn(BaseModel):
	images: List[str]
	language: LanguageEnum = 'en'
	level: LevelEnum = 'word'
	modality: ModalityEnum = 'printed'

class OCROut(BaseModel):
	text: List[str]


class LayoutIn(BaseModel):
	image: str


class BoundingBox(BaseModel):
	x: int = Field( description='X coordinate of the upper left point of bbox')
	y: int = Field( description='Y coordinate of the upper left point of bbox')
	w: int = Field( description='width of the bbox (in pixel)')
	h: int = Field( description='height of the bbox (in pixel)')


class Region(BaseModel):
	bounding_box: BoundingBox
	label: Optional[str] = ''
	line: Optional[int] = Field(
		0,
		description='Stores the sequential line number of the para text starting from 1'
	)

class LayoutOut(BaseModel):
	regions: List[Region]
