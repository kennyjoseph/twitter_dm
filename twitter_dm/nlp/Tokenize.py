# -*- coding: utf-8 -*-

"""
This code provides utility functions on top of twokenize.

Most importantly, the Tweet class uses extract_tokens_twokenize_and_regex

This class has some arabic stuff specific to particular projects I'm working on.

There's probably a bunch of ways to make this better/faster.
"""

import HTMLParser
import string

import regex

import twokenize
from nlp_helpers import lemmatize

_arabic_stemmer = None
arabic_regex = regex.compile('[\u0600-\u06ff\u0750-\u077f\u08a0-\u08ff]+',regex.U)
POSSESSIVE_REGEX = regex.compile(u"['’′][^\s\.,?\"]*",regex.U)
remove_punctuation_map = dict((ord(char), None) for char in string.punctuation)


def arabic_stemmer():
    from nltk.stem.isri import ISRIStemmer
    global _arabic_stemmer
    if not _arabic_stemmer:
        _arabic_stemmer = ISRIStemmer()
    return _arabic_stemmer

def getNGrams(temp_tokens, size=2):
    #if len(temp_tokens) == 0:
    #    tempTokens = self.tokens
    grams = []
    for i in range(len(temp_tokens)-size+1):
        grams.append(' '.join(temp_tokens[i:i+size]))

    return grams



def extract_tokens_twokenize_and_regex(text,
                                       noise_tokens,
                                       gram_list=[],
                                       keep_hashtags_and_mentions=True,
                                       make_lowercase=True,
                                       do_lemmatize=True,
                                       remove_possessive=True,
                                       do_arabic_stemming=True):
    return extract_tokens(text,
                           twokenize.tokenize,
                           noise_tokens,
                           gram_list,
                           keep_hashtags_and_mentions,
                           make_lowercase,
                           do_lemmatize,
                           remove_possessive,
                           do_arabic_stemming,
                           )


def extract_tokens(text,
                   tokenizing_function,
                   noise_tokens = set(),
                   gram_list= [],
                   keep_hashtags_and_mentions=True,
                   make_lowercase=True,
                   do_lemmatize=True,
                   remove_possessive=True,
                   do_arabic_stemming=True,
                   ):
    """
    Extract any requested ngrams as tokens. Ngrams generated from raw text, no punctuation (hopefully),
    urls & single characters removed removed, # and @ prefixes removed.
    """

    text = HTMLParser.HTMLParser().unescape(text)

    tempTokens = [unicode(token) for token in tokenizing_function(text) if token[:4] != 'http' and len(token) > 1]
    if keep_hashtags_and_mentions:
        tempTokens = [token[1:] if token[0] == '#' or token[0] == '@' and len(token) > 1 else token for token in tempTokens]

    if make_lowercase:
        words = [token.lower() for token in tempTokens]
    else:
        words = tempTokens

    # remove commas or words containing commas, numbers
    words = [token for token in words if token not in noise_tokens and
                                        len(token) >= 1 and
                                        token.find(',') < 0 and
                                        not token.translate(remove_punctuation_map).isdigit()]

    # remove initial, terminal, or paired quotation marks from word boundaries
    quotes = u'\'"`‘“’”'
    words = [token[1:] if token[0] in quotes and (len(token) == 1 or token[1] in string.letters) else token for token in words]
    words = [token[:-1] if len(token) > 0 and token[-1] in quotes and token[0] in string.letters else token for token in words]

    if remove_possessive:
        ##remove simple english possessive
        words = [POSSESSIVE_REGEX.sub("",token) for token in words]

    tokens = words

    # If the tweet is in English, append lemmatized tokens using wordnet
    # If the tweet is in Arabic
    if do_lemmatize:
        for i in range(len(tokens)):
            temp = lemmatize(tokens[i])
            if temp is not None:
                tokens[i] = temp

        if do_arabic_stemming:
            for i in range(len(tokens)):
                if len(arabic_regex.findall(tokens[i])) > 0:
                    tokens[i] = arabic_stemmer().stem(tokens[i])

    tokens = [t for t in tokens if len(t) > 0]

    for gramSize in gram_list:
        new_grams = getNGrams(tempTokens, gramSize)

        # drop any n-grams that do not contain at least two non-stopwords
        for gram in new_grams:
            drop_gram = True
            valid_count = 0
            for token in gram.split(' '):
                if not (token in noise_tokens):
                    valid_count += 1
                    if valid_count > 1:
                        drop_gram = False
                        break
            if not drop_gram:
                tokens.append(gram)

    tokens = [t for t in tokens if len(t) > 0 and t not in noise_tokens]
    if make_lowercase:
        tokens = [t.lower() for t in tokens]
    return tokens

