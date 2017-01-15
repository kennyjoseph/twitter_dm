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
import TwitterUser


class Tweet:
    def __init__(self, jsn_or_string, do_tokenize=True,
                 do_parse_created_at=True,
                 store_json=False,
                 store_full_retweet_and_quote=True,
                 noise_tokens=set(),
                 **kwargs):
        """
        :param jsn_or_string: A json representation of a tweet, i.e. the output of json.loads(line) for a line of a file with
         tweets in it in json format, or a string that can be loaded with json.loads
        :param do_tokenize: whether or not to perform tokenization (which is very slow), default True
        :param do_parse_created_at: whether or not to parse the tweet date into a twitter datetime object
            (which is kind of slow), default True
        :param store_json: Whether or not to store the raw JSON for the tweet (weird but useful in some cases)
        :param store_full_retweet_and_quote: If true will store a Tweet() representation of retweets and quoted tweets
                if available in the tweet text. These tweets have the same arguments as those passed into the function
        :param noise_tokens: A list of noise tokens to ignore during tokenization (if you're tokenizing), default none
        :param kwargs: Any other keyword arguments to pass into the tokenization function
        :return:
        """

        if type(jsn_or_string) is dict:
            jsn = jsn_or_string
        else:
            jsn = json.loads(jsn_or_string)

        if 'delete' in jsn:
            # not actually a tweet
            self.id = None
            return

        # store raw json (yuck, but useful in some random cases
        if store_json:
            self.raw_json = jsn
        else:
            self.raw_json = None

        # Get tweet id
        self.id = get_id(jsn)
        # Basic replacement of html characters

        tweet_text = get_text_from_tweet_json(jsn)
        self.text = HTMLParser.HTMLParser().unescape(tweet_text)

        # TOKEN EXTRACTION
        if do_tokenize:
            self.tokens = Tokenize.extract_tokens_twokenize_and_regex(tweet_text,
                                                                      noise_tokens,
                                                                      **kwargs)
        else:
            self.tokens = None

        self.hashtags = get_hashtags(jsn)

        if 'entities' in jsn:
            self.urls = [entity['expanded_url'] for entity in jsn['entities']['urls']]
        else:
            self.urls = []

        # get new lang field in tweet
        if 'lang' in jsn:
            self.lang = jsn['lang']
        else:
            self.lang = 'none'

        self.geo = None
        self.coordinates = None
        self.latitude = None
        self.longitude = None
        if 'coordinates' in jsn and jsn['coordinates']:
            self.coordinates = jsn['coordinates']
            if self.coordinates['type'] == 'Point':
                self.longitude = self.coordinates['coordinates'][0]
                self.latitude = self.coordinates['coordinates'][1]
        elif 'geo' in jsn and jsn['geo']:
            self.geo = jsn['geo']
            if 'coordinates' in self.geo:
                self.longitude = self.coordinates['coordinates'][1]
                self.latitude = self.coordinates['coordinates'][0]

        self.place = lookup(jsn, 'place')

        self.geocode_info = get_geo_record_for_tweet(jsn)

        self.source = jsn['source']

        if do_parse_created_at:
            self.created_at = get_created_at(jsn)

            # weird junk date
            if self.created_at.year < 2000 or self.created_at.year > 2020:
                self.created_at = None
        else:
            self.created_at = jsn.get('created_at', None)

        self.user = None
        if 'user' in jsn:
            self.user = TwitterUser.TwitterUser(user_data_object=jsn['user'])

        # Handle mentions, retweets, reply
        self.mentions = get_mentions(jsn, True)
        self.mentions_sns = get_mentions(jsn, False)

        self.reply_to = get_reply_to(jsn, return_id=(True and 'id' in jsn['user']))
        # this is a better name but keeping both for backwards compatability
        self.reply_to_user_id = self.reply_to
        self.reply_to_sn = get_reply_to(jsn, return_id=False)
        # this is a better name but keeping both for backwards compatability
        self.reply_to_user_screenname = self.reply_to_sn
        if self.reply_to:
            self.in_reply_to_status_id = jsn.get('in_reply_to_status_id', None)
        self.retweeted = get_retweeted_user(jsn, return_id=(True and 'id' in jsn['user']))
        self.retweeted_sn = get_retweeted_user(jsn, return_id=False)
        self.retweeted_tweet = None
        if 'retweeted_status' in jsn and store_full_retweet_and_quote:
            self.retweeted_tweet = Tweet(jsn['retweeted_status'],
                                         do_tokenize=do_tokenize,
                                         do_parse_created_at=do_parse_created_at,
                                         store_json=store_json,
                                         store_full_retweet_and_quote=store_full_retweet_and_quote,
                                         noise_tokens=noise_tokens,
                                         **kwargs)

        # See if this tweet was the user's own and it got retweeted
        self.retweeted_user_tweet_count = get_retweeted_count(jsn)

        # See if this tweet was the user's own and it got favorited
        self.favorited_user_tweet_count = get_favorited_count(jsn)

        # Quoted tweet stuff
        self.is_quote = jsn.get('is_quote_status', False)
        self.quoted_status_id = None
        self.quoted_tweet = None
        if self.is_quote:
            self.quoted_status_id = jsn.get('quoted_status_id', None)
            if 'quoted_status' in jsn and store_full_retweet_and_quote:
                self.quoted_tweet = Tweet(jsn['quoted_status'],
                                          do_tokenize=do_tokenize,
                                          do_parse_created_at=do_parse_created_at,
                                          store_json=store_json,
                                          store_full_retweet_and_quote=store_full_retweet_and_quote,
                                          noise_tokens=noise_tokens,
                                          **kwargs)
            else:
                self.quoted_tweet = None

    def setTokens(self, tokens):
        assert isinstance(tokens, list)
        self.tokens = tokens

    def return_all_text(self):
        return (self.text if not self.is_quote or not self.quoted_tweet
                else self.text + " \"" + self.quoted_tweet.text + "\"")

    def return_all_tokens(self):
        return (self.tokens if not self.is_quote and self.quoted_tweet
                else self.tokens + self.quoted_tweet.tokens)


def get_text_from_tweet_json(jsn):
    txt = jsn['text'] if 'text' in jsn else jsn['full_text']
    ## hm ... bug in full_text field for RTs? Or they just explain it terribly
    ## either way, this is a "fix"
    if txt.endswith(u"…") and 'retweeted_status' in jsn:
        txt = u"RT @{un}: {text}".format(un=jsn['retweeted_status']['user']['screen_name'],
                                         text=jsn['retweeted_status']['full_text'] 
                                                if 'full_text' in jsn['retweeted_status']
                                                else  jsn['retweeted_status']['text'])
        # remove the link to the tweet from
        #txt = txt[:txt.rfind("https")-1]
    return txt


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


def get_tweets_from_gzip(fname, **args):
    zf = gzip.open(fname, 'rb')
    reader = codecs.getreader("utf-8")
    contents = reader(zf)
    return [Tweet(json.loads(l), **args) for l in contents]


def get_hashtags(tweet_json):
    text = get_text_from_tweet_json(tweet_json)
    if 'entities' in tweet_json:
        return [entity['text'].lower() for entity in tweet_json['entities']['hashtags']]
    else:
        # if its an old tweet, do it the hard way
        return [x for x in set(
            [t for t in tokenize(text) if t.startswith("#") and not t == "#"])]


def get_mentions(tweet_json, return_id=False):
    text = get_text_from_tweet_json(tweet_json)
    to_return = 'id' if return_id else 'screen_name'
    if 'entities' in tweet_json:
        return [entity[to_return] for entity in tweet_json['entities']['user_mentions'] if to_return in entity]
    else:
        # if its an old tweet, do it the hard way
        return [x for x in set(
            [t.replace("@", "") for t in tokenize(text) if t.startswith("@") and not t == "@"])]


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
