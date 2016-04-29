# -*- coding: utf-8 -*-

__author__ = 'kjoseph'

import re
from glob import glob
import cPickle as pickle
import codecs
from itertools import groupby
import string
from contextlib import closing
from itertools import chain, groupby
from sklearn.metrics import accuracy_score
import gzip
import numpy as np
from pkg_resources import *
import joblib
from ..nlp.nlp_helpers import *

EXPERT_NON_IDENTITIES = {'i','me',"i'd","i've","i'm","i'll","my","myself",
                         'u','you',"your","you're",
                         'we','us','our',"let's","they're",
                         "he","she",'his','her','him','shes','hes', "he's",
                         "others", "group of people","someone",'people',"anyone",
                         "everyone","y'all","humans", "human","human beings","nobody", "person","ppl",
                         "you guys",
                         'god','lord'
                         }

STOP_WORD_REGEX = re.compile("(^(the|a|an|your|my|those|you|this|his|her|these|those|their|our|some)[ ]+)|(#)",re.IGNORECASE|re.UNICODE)
POSSESSIVE_REGEX = re.compile(u"['’′]?[s]?['’′]?$",re.U|re.I)



def get_wordforms_to_lookup(obj):
    if remove_emoji(obj.text) == '':
        return {}
    orig = obj.text.lower().replace("'s","")
    cleaned_text = get_cleaned_text(obj.text.lower())
    cleaned_singular = get_cleaned_text(obj.singular_form)
    cleaned_lemma = get_cleaned_text(obj.lemma)
    to_ret = {}
    #specific order, for overwrites
    to_ret[cleaned_lemma]  = "clean_lemma"
    to_ret[cleaned_singular] = "clean_sing"
    to_ret[cleaned_text] = "clean_text"
    to_ret[orig] = "orig"
    #if len(cleaned_text) and cleaned_text[-1] == 's':
    #    to_ret[cleaned_text[:-1]] = 'no_s'

    spl = re.split("/|-",cleaned_text)
    if len(spl) > 1 and ' ' not in cleaned_text:
        for x in re.split("/",cleaned_text):
            to_ret[x] = 'cleaned_split'
    return to_ret


def extract_tarfile(tar_url, extract_path='.'):
    import tarfile
    print tar_url
    tar = tarfile.open(tar_url, 'r')
    for item in tar:
        tar.extract(item, extract_path)
        if item.name.find(".tgz") != -1 or item.name.find(".tar") != -1:
            extract(item.name, "./" + item.name[:item.name.rfind('/')])


def create_dp_text(dp_terms):
    dp_text = dp_terms[0]
    if len(dp_terms) == 1:
        return dp_text

    for term in dp_terms[1:]:
        if term not in string.punctuation:
            dp_text += ' '
        dp_text += term

    return dp_text

def get_identity_model_and_features():
    model_fn = resource_filename('twitter_dm', 'data/trained_identity_model.p')
    model = joblib.load(model_fn)
    feature_fn = resource_filename('twitter_dm', 'data/feature_names.p')
    feature = joblib.load(feature_fn)
    return model, feature
