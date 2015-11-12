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
emoji_block0 = re.compile(u'[\u2600-\u27BF]')
emoji_block1 = re.compile(u'[\uD83C][\uDF00-\uDFFF]')
emoji_block2 = re.compile(u'[\uD83D][\uDC00-\uDE4F]')
emoji_block3 = re.compile(u'[\uD83D][\uDE80-\uDEFF]')


def remove_emoji(text):
    for expr in [emoji_block0,emoji_block1,emoji_block3,emoji_block4]:
        text = expr.sub("", text)
    return text


def get_cleaned_text(text):
    try:
        return remove_emoji(text.lower().replace("'s","").strip(string.punctuation))
    except:
        return text

wnl = WordNetLemmatizer()
def lemmatize(text):
    return wnl.lemmatize(text)

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


def get_alternate_wordforms(text,do_lemmatize=True,do_slow_singular=False):
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
        to_ret.add(lemmatize(clean))

    spl = re.split("/|-",clean)
    if len(spl) > 1 and ' ' not in clean:
        to_ret |= set(spl)
    return to_ret