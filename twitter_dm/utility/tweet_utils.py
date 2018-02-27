#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utilities that are frequently used in the context of a particular tweet or a set of Tweets
"""

import os
from datetime import datetime
import re
from pkg_resources import resource_stream


def get_all_associated_users_for_tweet(t):
    all_users = []

    # get all mentions in quoted tweet
    quote_users = []
    if t.quoted_tweet:
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
    all_users.append(str(t.retweeted))
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




bad_chars = re.compile('[\r\n\t]+')
def get_text_field(json):
    txt = ''
    if 'extended_tweet' in json and 'full_text' in json['extended_tweet']:
        txt = json['extended_tweet']['full_text']
    elif 'full_text' in json:
        txt = json['full_text']
    else:
        txt = json.get('text', '')
    return bad_chars.sub(' ', txt)

def get_text_from_tweet_json(jsn):
    txt = get_text_field(jsn)
    ## hm ... bug in full_text field for RTs? Or they just explain it terribly
    ## either way, this is a "fix"
    if txt.endswith(u"…") and 'retweeted_status' in jsn:
        txt = u"RT @{un}: {text}".format(un=jsn['retweeted_status']['user']['screen_name'],
                                         text=jsn['retweeted_status']['full_text']
                                         if 'full_text' in jsn['retweeted_status']
                                         else  jsn['retweeted_status']['text'])
    return txt


def us_geocode_tweet(tweet):
    import tweet_geocode

    if tweet.geocode_info is not None:
        geo_info = tweet_geocode.geocode_us_county(tweet.geocode_info)
        return {"lon": geo_info['lonlat'][0],
                "lat": geo_info['lonlat'][1],
                "county": lookup(geo_info, 'us_county.namelsad'),
                "state": lookup(geo_info, 'us_state.abbrev'),
                "loctype": geo_info['loc_type']
                }
    return None


def world_geocode_tweet(tweet):
    import tweet_geocode

    if tweet.geocode_info is not None:
        geo_info = tweet_geocode.geocode_world_country(tweet.geocode_info)
        return {"lon": geo_info['lonlat'][0],
                "lat": geo_info['lonlat'][1],
                "country": lookup(geo_info, 'country'),
                }
    return None


OneCoord = r'([-+]?\d{1,3}\.\d{3,})'
Separator = r', ?'
LatLong = re.compile(OneCoord + Separator + OneCoord, re.U)


def get_geo_record_for_tweet(tweet):
    is_coordinates = True
    geo = lookup(tweet, 'coordinates')
    if not geo:
        is_coordinates = False
        geo = lookup(tweet, 'geo')

    if geo and geo['type'] == 'Point':
        if is_coordinates:
            lon, lat = geo['coordinates']
        else:
            lat, lon = geo['geo']
        loc_type = 'OFFICIAL'
    else:
        loc = lookup(tweet, 'user.location').strip()
        if not loc:
            return None
        m = LatLong.search(loc.encode('utf8'))
        if not m:
            return None
        lat, lon = m.groups()
        loc_type = 'REGEX'
    try:
        lat = float(lat)
        lon = float(lon)
    except ValueError:
        return None

    if (lat, lon) == (0, 0) or lat < -90 or lat > 90 or lon < -180 or lon > 180:
        return None

    record = {}
    record['lonlat'] = [lon, lat]
    record['loc_type'] = loc_type
    record['user_location'] = lookup(tweet, 'user.location')
    return record


def get_retweeted_user(tweet_json, return_id=False):
    to_return = 'id' if return_id else 'screen_name'
    text = get_text_from_tweet_json(tweet_json)

    if 'retweeted_status' in tweet_json and 'user' in tweet_json['retweeted_status']:
        return tweet_json['retweeted_status']['user'][to_return]

    # If there is one user mention, then return it, otherwise return noting
    if 'RT' in text and 'entities' in tweet_json and len(tweet_json['entities']['user_mentions']) == 1:
        return tweet_json['entities']['user_mentions'][0][to_return]

    return None


def get_reply_to(line, return_id=False):
    #if 'in_reply_to_status_id' not in line or \
    #                        'in_reply_to_status_id' in line and line['in_reply_to_status_id'] is None:
    #    return None

    if not return_id:
        if 'in_reply_to_screen_name' in line:
            return line['in_reply_to_screen_name']
        return None

    if 'in_reply_to_user_id_str' in line and line['in_reply_to_user_id_str'] is not None:
        return line['in_reply_to_user_id_str']

    if 'in_reply_to_user_id' in line and line['in_reply_to_user_id'] is not None:
        return line['in_reply_to_user_id']
    return None

def get_id(jsn):
    if 'id_str' in jsn:
        return int(jsn['id_str'])
    if 'id' in jsn:
        return jsn['id']
    return None


def get_retweeted_count(jsn):
    if ('retweeted_status' not in jsn and 'quoted_status' not in jsn and
                'retweet_count' in jsn and
                jsn['retweet_count'] is not None and jsn['retweet_count'] > 0):
        return jsn['retweet_count']
    return 0


def get_favorited_count(jsn):
    if ('retweeted_status' not in jsn and 'quoted_status' not in jsn and
                'favorite_count' in jsn and
                jsn['favorite_count'] is not None and jsn['favorite_count'] > 0):
        return jsn['favorite_count']
    return 0


def get_created_at(jsn):
    if 'created_at' in jsn:
        return parse_date(jsn['created_at'])
    elif 'timestamp' in jsn:
        return datetime.utcfromtimestamp(jsn['timestamp'] / 1000)
    return None

def get_ext_status_ents(status):
    if status is None:
        return {}

    if 'extended_tweet' in status:
        return lookup(status, 'extended_tweet.entities', list())
    elif 'entities' in status:
        return status['entities']
    return None

def get_hashtags(tweet_json):
    text = get_text_from_tweet_json(tweet_json)
    entities = get_ext_status_ents(tweet_json)
    if entities:
        return [entity['text'].lower() for entity in entities['hashtags']]
    else:
        # if its an old tweet, do it the hard way
        return [x for x in set(
            [t for t in text.split() if t.startswith("#") and not t == "#"])]


def get_mentions(tweet_json, return_id=False):
    text = get_text_from_tweet_json(tweet_json)
    to_return = 'id' if return_id else 'screen_name'
    entities = get_ext_status_ents(tweet_json)
    if entities:
        return [entity[to_return] for entity in entities['user_mentions'] if to_return in entity]
    else:
        # if its an old tweet, do it the hard way
        return [x for x in set(
            [t.replace("@", "") for t in text.split() if t.startswith("@") and not t == "@"])]

