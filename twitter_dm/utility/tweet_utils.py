#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utilities that are frequently used in the context of a particular tweet or a set of Tweets
"""

from datetime import datetime
import os
import re
from pkg_resources import resource_stream


def get_ext_status_ents(status):
    if status is None:
        return {}
    if 'extended_tweet' in status:
        return lookup(status, 'extended_tweet.entities', list())
    elif 'entities' in status:
        return status['entities']
    return []

def get_all_associated_users_for_tweet(t):
    all_users = []

    # get all mentions in quoted tweet
    quote_users = []
    if t.is_quote and t.quoted_tweet:
        quote_users = get_all_associated_users_for_tweet(t.quoted_tweet)

    # get all mentions in retweeted tweet
    rt_users = []
    if t.retweeted_tweet:
        rt_users = get_all_associated_users_for_tweet(t.retweeted_tweet)

    # any "mentions" in the media content
    media_srcs = {str(m['source_user_id']) for m in t.media if 'source_user_id' in m}
    all_users += list(media_srcs)

    # get anyone being replied to
    if t.reply_to_user_id:
        all_users.append(str(t.reply_to_user_id))

    # add sender of tweet
    all_users.append(str(t.user.id))

    all_users += [str(x) for x in t.mentions]

    return all_users + quote_users + rt_users

def get_stopwords():
    stopwords_stream = resource_stream('twitter_dm', 'data/stopwords.txt')
    return set([word.strip() for word in stopwords_stream.readlines()])


def working_path(*args):
    return os.path.normpath(os.path.join(*args))


def parse_date(twitter_lame_datetime_string):
    """Twitter date string ('created_at' field) -> time object"""
    from datetime import datetime
    return datetime.strptime(twitter_lame_datetime_string, "%a %b %d %H:%M:%S +0000 %Y")


def get_date(myjson_object):
    """Returns the date string of the supplied tweet (YYYY-MM-DD)"""
    from datetime import datetime
    if 'created_at' in myjson_object:
        parsed_date= parse_date(myjson_object['created_at'])
        return parsed_date.strftime("%Y-%m-%d")
    if 'timestamp' in myjson_object:
        return datetime.utcfromtimestamp(myjson_object['timestamp']/1000).strftime("%Y-%m-%d")
    return None


#######STOLEN FROM BRENDAN############
def lookup(myjson, k,null_val=""):
  # return myjson[k]
  if '.' in k:
    # jpath path
    ks = k.split('.')
    v = myjson
    for k in ks: v = v.get(k,{})
    return v or null_val
  return myjson.get(k,null_val)

def get_time(myjson_object):
    if 'created_at' in myjson_object:
        parsed_date= parse_date(myjson_object['created_at'])
        return parsed_date.strftime("%H:%M:%S")
    if 'timestamp' in myjson_object:
        return datetime.utcfromtimestamp(myjson_object['timestamp']/1000).strftime("%H:%M:%S")
    return None


# TODO: remove
############FOR MINERVA, REMOVE AT SOME POINT


def regex_or(*items):
    return '(?:' + '|'.join(items) + ')'

punctChars = r"['\"“”‘’.?!…,:;]"
entity     = r"&(?:amp|lt|gt|quot);"
urlStart1  = r"(?:https?://|\bwww\.)"
commonTLDs = r"(?:com|org|edu|gov|net|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|pro|tel|travel|xxx)"
ccTLDs	 = r"(?:ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|" + \
r"bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|" + \
r"er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|" + \
r"hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|" + \
r"lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|" + \
r"nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|sk|" + \
r"sl|sm|sn|so|sr|ss|st|su|sv|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|" + \
r"va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|za|zm|zw)"	# TODO: remove obscure country domains?
urlStart2  = r"\b(?:[A-Za-z\d-])+(?:\.[A-Za-z0-9]+){0,3}\." + regex_or(commonTLDs, ccTLDs) + r"(?:\."+ccTLDs+r")?(?=\W|$)"
urlBody    = r"(?:[^\.\s<>][^\s<>]*?)?"
urlExtraCrapBeforeEnd = regex_or(punctChars, entity) + "+?"
urlEnd     = r"(?:\.\.+|[<>]|\s|$)"
url        = re.compile(regex_or(urlStart1, urlStart2) + urlBody + "(?=(?:"+urlExtraCrapBeforeEnd+")?"+urlEnd+")")


mention_pattern=re.compile(u"@([^~!@#$%^&*()_+`=/?,.<> ])*")
punctuation_pattern=re.compile(u"[~!@#$%^&*()_+`=/?,.<>: 0123456789 '\"“”‘’…;-]")


bin_size = 100


# return english percentage in integers
def GetStatistics(text, silence):
    import string
    orig_text = text
    text = url.sub("", text)
    text = text.replace("RT", "")
    text = mention_pattern.sub("", text)
    text = punctuation_pattern.sub("", text)

    char_count = len(text)
    english_count = 0
    for ch in text:
        # print ch
        if ch in string.printable:
            english_count += 1
    if not silence:
        print("orig text:", orig_text)
        print("\ttext=", text)
        print("\tlength=", len(text), english_count*bin_size/char_count, bin_size-english_count*bin_size/char_count)

    if char_count == 0:
        return 1
    else:
        return english_count*bin_size/char_count


def classify_language(text, cutoff=95, silence=True):
    english_percentage = GetStatistics(text, silence)
    if english_percentage >= cutoff:
        return "en"
    elif english_percentage <= (100-cutoff):
        return "ar"
    else:
        return "mix"
