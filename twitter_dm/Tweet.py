#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This file contains the Tweet class, which is the way we deal with and play with Tweets in this package

It also contains code to do geocoding if you've installed the geocoding package on my github repo at

https://github.com/kennyjoseph/twitter_geo_preproc


Note that a lot of the code is ugly because it deals with both the "new" and "old" (pre-2010, I believe)
tweet formats. It needs way more commenting, but that will come, I hope, soon.
"""


from .utility.tweet_utils import parse_date, lookup
import re
from datetime import datetime
import HTMLParser
import ujson as json
import gzip
import codecs
from nlp import Tokenize
from nlp.twokenize import tokenize


class Tweet:
    def __init__(self, jsn, do_tokenize=True,
                 store_json=False,
                 noise_tokens=set(),
                 **kwargs):

        # store raw json (yuck, but useful in some random cases
        if store_json:
            self.raw_json = jsn
        else:
            self.raw_json = None

        # Get tweet id
        self.id = get_id(jsn)
        # Basic replacement of html characters
        self.text = HTMLParser.HTMLParser().unescape(jsn['text'])

        # TOKEN EXTRACTION
        if do_tokenize:
            self.tokens = Tokenize.extract_tokens_twokenize_and_regex(jsn['text'],
                                                             noise_tokens,
                                                             **kwargs)
        else:
            self.tokens = None

        self.hashtags = get_hashtags(jsn)

        if 'entities' in jsn:
            self.urls = [entity['expanded_url'] for entity in jsn['entities']['urls']]
        else:
            self.urls = []

        self.geo = None
        if 'geo' in jsn and jsn['geo']:
            self.geo = jsn['geo']['coordinates']

        self.geocode_info = get_geo_record_for_tweet(jsn)

        self.created_at = get_created_at(jsn)

        # weird junk date
        if self.created_at.year < 2000 | self.created_at.year > 2020:
            self.created_at = None

        self.user = dict(id=get_id(jsn['user']),
                         screen_name=lookup(jsn, 'user.screen_name'),
                         followers=lookup(jsn, 'user.followers_count', None),
                         friends=lookup(jsn, 'user.friends_count', None),
                         verified=lookup(jsn, 'user.verified', None),
                         utc_offset=lookup(jsn, 'user.utc_offset', None))

        # Handle mentions, retweets, reply
        self.mentions = get_mentions(jsn, True)
        self.mentions_sns = get_mentions(jsn, False)

        self.reply_to = get_reply_to(jsn, return_id=(True and 'id' in jsn['user']))
        self.reply_to_sn = get_reply_to(jsn, return_id=False)
        self.retweeted = get_retweeted_user(jsn, return_id=(True and 'id' in jsn['user']))
        self.retweeted_sn = get_retweeted_user(jsn, return_id=False)

        # See if this tweet was the user's own and it got retweeted
        self.retweeted_user_tweet_count = get_retweeted_count(jsn)

    def setTokens(self, tokens):
        assert isinstance(tokens, list)
        self.tokens = tokens


def us_geocode_tweet(tweet):
    import tweet_geocode

    if tweet.geocode_info is not None:
        geo_info = tweet_geocode.geocode_us_county(tweet.geocode_info)
        return {"lon": geo_info['lonlat'][1],
                "lat": geo_info['lonlat'][0],
                "county": lookup(geo_info, 'us_county.namelsad'),
                "state": lookup(geo_info, 'us_state.abbrev'),
                "loctype": geo_info['loc_type']
                }
    return None


def world_geocode_tweet(tweet):
    import tweet_geocode

    if tweet.geocode_info is not None:
        geo_info = tweet_geocode.geocode_world_country(tweet.geocode_info)
        return {"lon": geo_info['lonlat'][1],
                "lat": geo_info['lonlat'][0],
                "country": lookup(geo_info, 'country'),
                }
    return None


OneCoord = r'([-+]?\d{1,3}\.\d{3,})'
Separator = r', ?'
LatLong = re.compile(OneCoord + Separator + OneCoord, re.U)


def get_geo_record_for_tweet(tweet):
    geo = lookup(tweet, 'geo')
    if geo and geo['type'] == 'Point':
        lat, lon = geo['coordinates']
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


def get_tweets_from_gzip(fname, **args):
    zf = gzip.open(fname, 'rb')
    reader = codecs.getreader("utf-8")
    contents = reader(zf)
    return [Tweet(json.loads(l), **args) for l in contents]


def get_hashtags(tweet_json):
    if 'entities' in tweet_json:
        return [entity['text'].lower() for entity in tweet_json['entities']['hashtags']]
    else:
        # if its an old tweet, do it the hard way
        return [x for x in set(
            [t for t in tokenize(tweet_json['text']) if t.startswith("#") and not t == "#"])]


def get_mentions(tweet_json, return_id=False):
    to_return = 'id' if return_id else 'screen_name'
    if 'entities' in tweet_json:
        return [entity[to_return] for entity in tweet_json['entities']['user_mentions'] if to_return in entity]
    else:
        # if its an old tweet, do it the hard way
        return [x for x in set(
            [t.replace("@", "") for t in tokenize(tweet_json['text']) if t.startswith("@") and not t == "@"])]


def get_retweeted_user(tweet_json, return_id=False):
    to_return = 'id' if return_id else 'screen_name'

    if 'retweeted_status' in tweet_json and 'user' in tweet_json['retweeted_status']:
        return tweet_json['retweeted_status']['user'][to_return]

    # If there is one user mention, then return it, otherwise return noting
    if 'RT' in tweet_json['text'] and 'entities' in tweet_json and len(tweet_json['entities']['user_mentions']) == 1:
        return tweet_json['entities']['user_mentions'][0][to_return]

    return None


def get_reply_to(line, return_id=False):
    if 'in_reply_to_status_id' not in line or \
                            'in_reply_to_status_id' in line and line['in_reply_to_status_id'] == None:
        return None

    if not return_id:
        if 'in_reply_to_screen_name' in line:
            return line['in_reply_to_screen_name']
        return None

    if 'in_reply_to_user_id_str' in line and line['in_reply_to_user_id_str'] is not None:
        return line['in_reply_to_user_id_str']

    if 'in_reply_to_user_id' in line and line['in_reply_to_user_id'] is not None:
        return line['in_reply_to_user_id']


def get_id(jsn):
    if 'id_str' in jsn:
        return int(jsn['id_str'])
    if 'id' in jsn:
        return jsn['id']
    return None


def get_retweeted_count(jsn):
    if 'retweeted_status' not in jsn and \
                    'retweet_count' in jsn and \
                    jsn['retweet_count'] is not None and jsn['retweet_count'] > 0:
        return jsn['retweet_count']
    return 0


def get_created_at(jsn):
    if 'created_at' in jsn:
        return parse_date(jsn['created_at'])
    elif 'timestamp' in jsn:
        return datetime.utcfromtimestamp(jsn['timestamp'] / 1000)
    return None