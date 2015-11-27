import re
import string
from nltk.stem.wordnet import WordNetLemmatizer
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


def remove_emoji(text):
    for expr in [_emoji_block0,_emoji_block1,_emoji_block2,_emoji_block3]:
        text = expr.sub("", text)
    return text


def get_cleaned_text(text):
    try:
        return remove_emoji(text.lower().replace("'s","").strip(string.punctuation))
    except:
        return text

_wnl = None

def lemmatize(text,pos=None):
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
    elif text.endswith("s"):
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
        s_val = eng.singular_noun(text)
        if not s_val:
            return text
        return s_val
    except:
        pass
    return text


def get_alternate_wordforms(text,do_lemmatize=True,do_slow_singular=False,pos_tag=None):
    to_ret = set()

    clean = get_cleaned_text(text.lower()).replace("'s","")
    if clean == '':
        return to_ret
    to_ret.add(clean)

    if do_slow_singular:
        to_ret.add(get_singular_slow(clean))
    else:
        to_ret.add(get_singular_fast(clean))

    if do_lemmatize:
        if pos_tag:
            to_ret.add(lemmatize(clean,pos_tag))
        else:
            to_ret.add(lemmatize(clean))

    spl = re.split("/|-",clean)
    if len(spl) > 1 and ' ' not in clean:
        to_ret |= set(spl)
    return to_ret