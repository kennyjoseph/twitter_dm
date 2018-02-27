#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This file contains the Tweet class, which is the way we deal with and play with Tweets in this package

It also contains code to do geocoding if you've installed the geocoding package on my github repo at

https://github.com/kennyjoseph/twitter_geo_preproc


Note that a lot of the code is ugly because it deals with both the "new" and "old" (pre-2010, I believe)
tweet formats. It needs way more commenting, but that will come, I hope, soon.
"""

import HTMLParser
import arrow
from bs4 import BeautifulSoup
import ujson as json
import gzip
import codecs
import TwitterUser
from nlp import Tokenize
from .utility.tweet_utils import *
from nlp.twokenize import tokenize


class Tweet:
    def __init__(self, jsn_or_string,
                 do_tokenize=True,
                 do_parse_created_at=True,
                 store_json=False,
                 store_full_retweet_and_quote=True,
                 noise_tokens=set(),
                 do_parse_source=False,
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

        if 'delete' in jsn or ('text' not in jsn and 'full_text' not in jsn):
            # not actually a tweet
            self.id = None
            return

        ################ Basic Stuff #######################################
        # store raw json (yuck, but useful in some random cases)
        if store_json:
            self.raw_json = jsn
        else:
            self.raw_json = None

        # Get tweet id
        self.id = get_id(jsn)

        # Get User info
        self.user = None
        if 'user' in jsn:
            self.user = TwitterUser.TwitterUser(user_data_object=jsn['user'])

        # so I don't have to try to remember each time whether its an int or string
        self.id_int = int(self.id)
        self.id_str = str(self.id)

        # get new lang field in tweet
        self.lang = lookup(jsn, 'lang')

        # get overall retweet count (i.e. ignore whether this is an original tweet)
        self.retweet_count = jsn.get('retweet_count', 0)
        self.quote_count = lookup(jsn,"quote_count",0)
        self.reply_count = lookup(jsn,"reply_count",0)
        self.favorited_count = jsn.get('favorite_count', 0)

        #######################################################

        ################ Text Stuff #######################################
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
        #######################################################


        ################ (Extended) Entities #######################################
        self.entities = get_ext_status_ents(jsn)
        self.hashtags = get_hashtags(jsn)
        self.mentions = get_mentions(jsn, True)
        self.mentions_sns = get_mentions(jsn, False)
        self.urls = [x['expanded_url'] for x in self.entities.get("urls")]
        self.media = lookup(jsn, 'extended_entities.media', []) + lookup(jsn,'entities.media',[])
        #######################################################

        ################ GEO #######################################
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
        #######################################

        ################ Source Field #######################################
        self.source = jsn['source']
        if do_parse_source:
            source_info = BeautifulSoup(self.source, 'html.parser').a
            try:
                self.source_link = source_info.get("href")
                self.source_name = source_info.text
            except:
                self.source_link = None
                self.source_name = None
        #######################################################

        ################ Datetime stuff #######################################
        if do_parse_created_at:
            self.created_at = get_created_at(jsn)
            # weird junk date
            if self.created_at.year < 2000 or self.created_at.year > 2020:
                self.created_at = None

            if lookup(jsn, 'user.utc_offset', None):
                self.local_time = arrow.get(arrow.get(self.created_at).timestamp + jsn['user']['utc_offset'])
            else:
                self.local_time = None

        else:
            self.created_at = jsn.get('created_at', None)
        ####################################################################

        ################### Retweet Stuff###################################
        self.retweeted_tweet = None
        if 'retweeted_status' in jsn and store_full_retweet_and_quote:
            self.retweeted_tweet = Tweet(jsn['retweeted_status'],
                                         do_tokenize=do_tokenize,
                                         do_parse_created_at=do_parse_created_at,
                                         store_json=store_json,
                                         store_full_retweet_and_quote=store_full_retweet_and_quote,
                                         noise_tokens=noise_tokens,
                                         **kwargs)

        # TRY NOT TO USE THIS STUFF ANYMORE, DO EVERYTHING THROUGH THE RT OBJECT
        # See if this tweet was the user's own and it got retweeted
        self.retweeted_user_tweet_count = get_retweeted_count(jsn)
        self.retweeted = get_retweeted_user(jsn, return_id=(True and 'id' in jsn['user']))
        self.retweeted_sn = get_retweeted_user(jsn, return_id=False)
        ####################################################################

        ################### Reply Stuff###################################
        self.reply_to = get_reply_to(jsn, return_id=(True and 'id' in jsn['user']))
        # this is a better name but keeping both for backwards compatability
        self.reply_to_user_id = self.reply_to
        self.reply_to_sn = get_reply_to(jsn, return_id=False)
        # this is a better name but keeping both for backwards compatability
        self.reply_to_user_screenname = self.reply_to_sn
        self.in_reply_to_status_id = None
        if self.reply_to:
            self.in_reply_to_status_id = jsn.get('in_reply_to_status_id', None)
        ####################################################################

        ################### Quote Stuff ###################################
        # Quoted tweet stuff - we will only get a quote of a RT if we're storing the RT!
        self.is_retweet_of_quote = (jsn.get('is_quote_status', False) and
                                    'quoted_status' not in jsn and
                                    'retweeted_status' in jsn)
        self.quoted_tweet = None
        self.quoted_status_id = None
        # There are some inexplicable conditions in which it is a quote tweet but we don't get sent the quoted tweet info
        if 'quoted_status' in jsn:
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
        ####################################################################

        ################### All connected users stuff ###################################
        self.all_connected_users = set([x for x in get_all_associated_users_for_tweet(self) if x != self.id])
        ####################################################################

    def setTokens(self, tokens):
        assert isinstance(tokens, list)
        self.tokens = tokens

    def return_all_text(self):
        return (self.text if not self.is_quote or not self.quoted_tweet
                else self.text + " \"" + self.quoted_tweet.text + "\"")

    def return_all_tokens(self):
        return (self.tokens if not self.is_quote and self.quoted_tweet
                else self.tokens + self.quoted_tweet.tokens)



def get_tweets_from_gzip(fname, **args):
    zf = gzip.open(fname, 'rb')
    reader = codecs.getreader("utf-8")
    contents = reader(zf)
    return [Tweet(json.loads(l), **args) for l in contents]


