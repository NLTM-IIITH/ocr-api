import base64
import json

from fastapi import APIRouter

from .helper import infer, preprocess
from .models import PostprocessRequest

router = APIRouter(
    prefix='/ocr/postprocess',
    tags=['PostProcess'],
)


@router.post(
    '/',
    response_model_exclude_none=True
)
async def postprocess_ocr(req: PostprocessRequest):
    lexicon = req.lexicon
    if isinstance(lexicon, str):
        lexicon = open(f'./server/modules/postprocess/lexicons/{lexicon}.txt', 'r', encoding='utf-8').read().strip()
        lexicon = lexicon.split('\n')
        lexicon = [i[0] for i in lexicon if len(i) > 1]
    if isinstance(req.vocabulary, str):
        vocabulary = req.vocabulary
        while '\n' in vocabulary:
            vocabulary = vocabulary.replace('\n', ' ')
        while '  ' in vocabulary:
            vocabulary = vocabulary.replace('  ', ' ')
        vocabulary = vocabulary.strip().split(' ')
    else:
        vocabulary = req.vocabulary
    lexicon_groups, vocabulary_trie = preprocess(lexicon, vocabulary)
    result = []
    words = req.words
    for i in range(len(words)):
        max_prob = words[i]["meta"]["max_prob"]
        max_prob = base64.b64decode(max_prob)
        max_prob = max_prob.decode('utf-8').split("\n")
        max_prob = [int(float(i)) for i in max_prob if i]
        data_prob = words[i]["meta"]["data_prob"]
        data_prob = base64.b64decode(data_prob)
        data_prob_strs = data_prob.decode('utf-8').split("\n")
        data_prob = []
        for row in data_prob_strs:
            if row:
                data_prob_row = row.split(",")
                data_prob_row = [float(i) for i in data_prob_row if i]
                data_prob.append(data_prob_row)
        pred = words[i]["text"]
        suggestions = infer(lexicon, lexicon_groups, vocabulary_trie, pred, max_prob, data_prob, 20)
        result.append({"raw_ocr": pred, "suggestions": suggestions})
    return result
    # result = json.dumps(result, ensure_ascii=False)

