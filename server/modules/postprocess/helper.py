import unicodedata

import editdistance

from server.modules.postprocess import trie_implementation


def clean(word: str, lexicon_groups) -> str:
    clean_word = ""
    for letter in word:
        if letter in lexicon_groups["punc"]:
            continue
        clean_word = clean_word + letter
    return clean_word

def character_classifier(lexicon: list):
    lexicon_groups = {"punc": [], "submatra": [], "matra": [], "enums": [], "nums": [], "cons": [], "vows": [], "eng": []}
    letter = []
    for l in lexicon:
        try:
            name = unicodedata.name(l)
        except:
            name = ""
        
        if "LATIN" in name:
            lexicon_groups["eng"].append(l)
        elif "DIGIT" in name:
            if len(name.split()) == 2:
                lexicon_groups["enums"].append(l)
            else:
                lexicon_groups["nums"].append(l)
        elif "VOWEL" in name:
            lexicon_groups["matra"].append(l)
        elif "LETTER" in name:
            letter.append(l)
        else:
            lexicon_groups["punc"].append(l)
        
    ll = (ord(letter[0]) >> 4) << 4
    ul = ord(lexicon_groups["nums"][0])
        
    for l in lexicon_groups["punc"]:
        if l != "":
            print(f'"{l}"', len(l))
            if ord(l) < ul and ord(l) >= ll:
                lexicon_groups["submatra"].append(l)

    for l in lexicon_groups["submatra"]:
        lexicon_groups["punc"].remove(l)
    
    for l in letter:
        if ord(l) - ord(letter[0]) >= 16:
            lexicon_groups["cons"].append(l)
        else:
            lexicon_groups["vows"].append(l)
            
    return lexicon_groups
            
def build_vocab_trie(vocabulary: list, lexicon: list):    
    vocabulary.extend(lexicon)
    vocabulary = list(set(vocabulary))
    vocab_trie = trie_implementation.Node()
    vocab_trie.insert_list(vocabulary)
    return vocab_trie

def condense_probability_data(lexicon, max_prob, data_prob):
    max_prob_ind = 0
    prob_ind = -1
    prob = []
    cur_char = trie_implementation.blank_char
    while True:
        if max_prob_ind == len(max_prob):
            break
        if max_prob[max_prob_ind] == 0:
            max_prob_ind += 1
            cur_char = trie_implementation.blank_char
            continue
        if lexicon[max_prob[max_prob_ind]] == cur_char:
            for i in range(len(data_prob[0])):
                prob[prob_ind][i] *= data_prob[max_prob_ind][i]
            max_prob_ind += 1
        else:
            prob.append(data_prob[max_prob_ind])
            cur_char = lexicon[max_prob[max_prob_ind]]
            max_prob_ind += 1
            prob_ind += 1
    return prob  

def get_max_prob_words(data_prob, lex_len, lex, lex_groups, beam_width=20) -> list:
    word_list = [] # final list to return
    
    for i in range(len(data_prob)):
        curr = word_list
        word_list = []
        ind = sorted(range(lex_len), key=lambda x: -data_prob[i][x])[:beam_width]
        
        if len(curr) == 0:
            word_list = [[lex[index], data_prob[i][index]] for index in ind if lex[index] in lex_groups["punc"] + lex_groups["nums"] + lex_groups["cons"] + lex_groups["vows"]]
        else:
            for word in curr:
                if len(word[0]) == 0:
                    for index in ind:
                        if lex[index] in lex_groups["punc"] + lex_groups["nums"] + lex_groups["cons"] + lex_groups["vows"]:
                            word_list.append([lex[index], data_prob[i][index]])
                    continue
                for index in ind:
                    last_letter = word[0][-1]
                    cur_letter = lex[index]
                    if cur_letter in lex_groups["eng"] + lex_groups["enums"] + [trie_implementation.blank_char]:
                        continue
                    if cur_letter in lex_groups["submatra"] and last_letter not in lex_groups["matra"] + lex_groups["cons"] + lex_groups["vows"]:
                        continue
                    if cur_letter in lex_groups["matra"] and last_letter not in lex_groups["cons"]:
                        continue
                    if cur_letter in lex_groups["nums"] and last_letter not in lex_groups["nums"]:
                        continue
                    if cur_letter in lex_groups["cons"] and last_letter not in lex_groups["punc"] + lex_groups["submatra"] + lex_groups["matra"] + lex_groups["cons"] + lex_groups["vows"]:
                        continue
                    if cur_letter in lex_groups["vows"] and last_letter not in lex_groups["punc"] + lex_groups["submatra"] + lex_groups["matra"] + lex_groups["cons"] + lex_groups["vows"]:
                        continue
                    word_list.append([word[0] + cur_letter, word[1] * data_prob[i][index]])
                    if cur_letter == "ं":
                        word_list.append([word[0] + "ँ", word[1] * data_prob[i][lex.index("ँ")]])
                    if cur_letter == "ँ":
                        word_list.append([word[0] + "ं", word[1] * data_prob[i][lex.index("ं")]])
            word_list = sorted(word_list, key=lambda x: -x[1])[:beam_width]
    return [word[0] for word in word_list]

def get_nearest_vocab_words(data_prob, lexicon, vocabulary, beam_width=20) -> list:
    queue = [[vocabulary, 1, 0]]
    final_list = []
    
    # print("lex = ", len(lexicon))
    # print("data prob = ", len(data_prob), len(data_prob[0]))
    
    word_list = []
    while len(queue) > 0:
        curr = queue[0]
        queue.pop(0)
        
        if(curr[2] >= len(data_prob)):
            continue
        
        num_in = 0
        for letter in lexicon:
            if letter in curr[0].children:
                num_in += 1
        
        normalize = 1
        if num_in > 0:
            normalize = len(lexicon)/num_in
        
        i = 0
        for letter in lexicon:
            if letter in curr[0].children and data_prob[curr[2]][i] > 0:
                word_list.append([curr[0].children[letter], data_prob[curr[2]][i] * curr[1] * normalize, curr[2]+1])
            i += 1
        
        if len(queue) == 0:
            word_list = sorted(word_list, key=lambda x: -x[1])
            queue = word_list[:beam_width]
            final_list.extend([ele[0].word for ele in queue if ele[0].is_end])
            word_list = []
    
    return final_list

def filter_by_distance(nearest_words: list, prediction: str, lexicon_groups, count: int = 5) -> list:
    words_with_scores = []
    temp = nearest_words
    nearest_words = []
    for word in temp:
        if word not in nearest_words:
            nearest_words.append(word)
    for word in nearest_words:
        if word == None:
            continue
        score = editdistance.eval(word, prediction)
        score_clean = editdistance.eval(clean(word, lexicon_groups), prediction)
        if score_clean < score:
            words_with_scores.append([clean(word, lexicon_groups), score_clean])
        else:
            words_with_scores.append([word, score])
    
    words_with_scores = sorted(words_with_scores, key=lambda x: x[1])
    words_with_scores = words_with_scores[:count]
    words_only = [word[0] for word in words_with_scores]
    return words_only

def preprocess(lexicon, vocabulary):
    lexicon_groups = character_classifier(lexicon)
    lexicon.insert(0, trie_implementation.blank_char)
    vocab_trie = build_vocab_trie(vocabulary, lexicon)
    return lexicon_groups, vocab_trie

def infer(lexicon, lexicon_groups, vocabulary, prediction, max_prob, data_prob, beam_width=20):
    lex_len = len(data_prob[0])
    data_prob = condense_probability_data(lexicon, max_prob, data_prob)
    nearest_vocab_words = get_nearest_vocab_words(data_prob, lexicon, vocabulary, beam_width)
    max_prob_words = get_max_prob_words(data_prob, lex_len, lexicon, lexicon_groups, beam_width)
    nearest_vocab_words = filter_by_distance(nearest_vocab_words, prediction, lexicon_groups)
    max_prob_words = filter_by_distance(max_prob_words, prediction, lexicon_groups)
    nearest_words = nearest_vocab_words + max_prob_words
    nearest_words = filter_by_distance(nearest_words, prediction, lexicon_groups, len(nearest_words))
    return nearest_words