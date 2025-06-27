
PORT = 8058
NUMBER_LOADED_MODEL_THRESHOLD = 2

IMAGE_FOLDER = '/home/ocr/website/images'

LANGUAGES = {
	'en': 'english',
	'hi': 'hindi',
	'mr': 'marathi',
	'ta': 'tamil',
	'te': 'telugu',
	'kn': 'kannada',
	'gu': 'gujarati',
	'pa': 'punjabi',
	'bn': 'bengali',
	'ml': 'malayalam',
	'asa': 'assamese',
	'mni': 'manipuri',
	'ori': 'oriya',
	'ur': 'urdu',

	'me': 'meetei',

	# Extra languages
	'brx': 'bodo',
	'doi': 'dogri',
	'ks': 'kashmiri',
	'kok': 'konkani',
	'mai': 'maithili',
	'ne': 'nepali',
	'sa': 'sanskrit',
	'sat': 'santali',
	'sd': 'sindhi',
}

SURYA_LANG = {
    'assamese': 'as',
    'bengali': 'bn',
    'english': 'en',
    'gujarati': 'gu',
    'hindi': 'hi',
    'kannada': 'kn',
    'malayalam': 'ml',
    'marathi': 'mr',
    'nepali': 'ne',
    'oriya': 'or',
    'punjabi': 'pa',
    'sanskrit': 'sa',
    'sindhi': 'sd',
    'tamil': 'ta',
    'telugu': 'te',
}

EASYOCR_LANG = {
    'assamese': 'as',
    'bengali': 'bn',
    'english': 'en',
    'hindi': 'hi',
    'kannada': 'kn',
    'marathi': 'mr',
    'maithili': 'mai',
    'nepali': 'ne',
	# There are some errors in tamil language for easyOCR
    # see: https://github.com/JaidedAI/EasyOCR/issues/1135
	# 'tamil': 'ta',
    'telugu': 'te',
    'urdu': 'ur'
}

TESS_LANG = {
	'english': 'eng',
	'hindi': 'hin',
	'marathi': 'mar',
	'tamil': 'tam',
	'telugu': 'tel',
	'kannada': 'kan',
	'gujarati': 'guj',
	'punjabi': 'pan',
	'bengali': 'ben',
	'malayalam': 'mal',
	'assamese': 'asm',
	'manipuri': 'ben',
	'oriya': 'ori',
	'urdu': 'urd',
    'nepali': 'nep',
    'sanskrit': 'san',
    'sindhi': 'snd',
    'kashmiri': 'hin',
}

MONGO_ENDPOINT = 'mongodb://admin:admin@127.0.0.1:27017/ocr'
MONGO_DATABASE = 'ocr'

AUTH_SECRET_KEY = "e7380eb69c18ea7399ac3135c97c9977e5c173077fa6988cd7ab731e904fb003"
AUTH_ALGORITHM = "HS256"
