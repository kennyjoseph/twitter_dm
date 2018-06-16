# -*- coding: utf-8 -*-
import re
import string

try:
    # UCS-4
    EMOTICONS = re.compile(u'[\U00010000-\U0010ffff]')
    EMOTICONS_2 = re.compile(u'[\u2700-\u27BF\u2600-\u26FF\u2300-\u23FF]')
except re.error:
    # UCS-2
    EMOTICONS = re.compile(u'[\uD800-\uDBFF][\uDC00-\uDFFF]')
    EMOTICONS_2 = re.compile(u'[\u2700-\u27BF\u2600-\u26FF\u2300-\u23FF]')
_emoji_block0 = re.compile(u'[\u2600-\u27BF]')
_emoji_block1 = re.compile(u'[\uD83C][\uDF00-\uDFFF]')
_emoji_block2 = re.compile(u'[\uD83D][\uDC00-\uDE4F]')
_emoji_block3 = re.compile(u'[\uD83D][\uDE80-\uDEFF]')


CRAP_CHAR_REPLACEMENT = {
    ord(u"\x85") : 8230,
    ord(u'\x96') : 8211,             # u'\u2013' en-dash
    ord(u'\x97') : 8212,             # u'\u2014' em-dash
    ord(u'\x91') : 8216,             # u'\u2018' left single quote
    ord(u'\x92') : 8217,             # u'\u2019' right single quote
    ord(u'\x93') : 8220,             # u'\u201C' left double quote
    ord(u'\x94') : 8221,             # u'\u201D' right double quote
    ord(u'\x95') : 8226              # u'\u2022' bullet
}

CRAP_CHAR_REMOVAL = {
    ord(u"\x85") : None,
    ord(u'\x96') : None,             # u'\u2013' en-dash
    ord(u'\x97') : None,             # u'\u2014' em-dash
    ord(u'\x91') : None,             # u'\u2018' left single quote
    ord(u'\x92') : None,             # u'\u2019' right single quote
    ord(u'\x93') : None,             # u'\u201C' left double quote
    ord(u'\x94') : None,             # u'\u201D' right double quote
    ord(u'\x95') : None              # u'\u2022' bullet
}


QUOTATION_REGEX = re.compile(u'[\'"`‘“’”’]')

def get_tweet_text_sub_emoticons(tweet):
    text = tweet.text
    for e in [_emoji_block3,_emoji_block0,_emoji_block1,_emoji_block3,EMOTICONS_2,EMOTICONS]:
        text = e.sub("*",text)
    return text

def remove_emoji(text):
    for expr in [_emoji_block0,_emoji_block1,_emoji_block2,_emoji_block3]:
        text = expr.sub("", text)
    return text.translate(CRAP_CHAR_REPLACEMENT)


def get_cleaned_text(text):
    try:
        return QUOTATION_REGEX.sub("",
                remove_emoji(
                    text.lower().replace("'s","").replace(u"\u2026","").strip(string.punctuation)).translate(CRAP_CHAR_REMOVAL))
    except:
        return text

_wnl = None

def lemmatize(text,pos=None):
    from nltk.stem.wordnet import WordNetLemmatizer
    global _wnl
    if not _wnl:
        _wnl = WordNetLemmatizer()
    if pos:
        return _wnl.lemmatize(text,pos)
    return _wnl.lemmatize(text)

singular_map = {"children" : "child",
                "men" : "man",
                "women" : "woman",
                "people" : "person"
                }

def get_singular_fast(text):
    if text in singular_map:
        return singular_map[text]
    elif text.endswith("s") and text != 'is':
        return text[:-1]
    elif text.endswith("'s") or text.endswith("s"):
        return text[:-2]
    return text


def get_singular_slow(text):
    import inflect
    global i_eng
    if not i_eng:
         i_eng = inflect.engine()
    try:
        s_val = i_eng.singular_noun(text)
        if not s_val:
            return text
        return s_val
    except:
        pass
    return text


def get_alternate_wordforms(text,do_lemmatize=True,do_slow_singular=False,pos_tag=None,lemmatized_wordform=None):
    to_ret = set()

    clean = get_cleaned_text(text.lower()).replace("'s","")
    if clean == '':
        return to_ret
    to_ret.add(clean)

    if do_slow_singular:
        to_ret.add(get_singular_slow(clean))
    else:
        to_ret.add(get_singular_fast(clean))

    if lemmatized_wordform:
        to_ret.add(lemmatized_wordform)
    elif do_lemmatize:
        if pos_tag:
            to_ret.add(lemmatize(clean,pos_tag))
        else:
            to_ret.add(lemmatize(clean))

    spl = re.split("/|-",clean)
    if len(spl) > 1 and ' ' not in clean:
        to_ret |= set(spl)
    return [x for x in to_ret if len(x)]

def search_text_for_topics(tweet_text,terms_to_topic_dictionary,max_n_gram_size=2):
    """
    :param tweet_text: Text of the tweet
    :param terms_to_topic_dictionary: A map from a term/phrase to a topic name
    :param max_n_gram_size: The size of the largest ngram you want to look at
    :return: a set() of topics found in the tweet
    """
    tokens = tokenize(tweet_text)
    tweet_topics = set()
    for i in range(len(tokens)):
        for j in range(0,min(max_ngram_size,len(tokens) - i)):
            curr_tokens = tokens[i:(i+j+1)]

            # get all alternate forms
            alt_forms = [get_alternate_wordforms(wf) for wf in curr_tokens]
            if any([not len(wf) for wf in alt_forms]):
                continue
            # Do dictionary lookups
            for comb in itertools.product(*alt_forms):
                ct =  " ".join(comb)
                if ct in term_to_topic:
                    tweet_topics.add(terms_to_topic_dictionary[ct])
    return tweet_topics