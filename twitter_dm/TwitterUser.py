"""A class to handle Twitter users.

The constructor takes in either a list of dictionary objects (from a json.loads of a .json file)
Or just a screen name/user_id and, optionally, an api_hook

If you do the latter and have an api_hook, then you can use the populate_* methods
to "hydrate" this user.  For example, populate_tweets_from_api() uses the api_hook
and goes to the Twitter API to get this user's tweets

..moduleauthor:: Kenneth Joseph <josephkena@gmail.com>

"""
__author__ = 'kjoseph'

import StringIO
import codecs
import datetime
import gzip
import io
import os
import random
import subprocess
import ujson as json
from collections import Counter

from pkg_resources import resource_stream

import Tweet
from .utility.general_utils import tab_stringify_newline as tsn
from .utility.tweet_utils import parse_date


class TwitterUser:
    def __init__(self, api_hook=None, screen_name=None, user_id=None, user_data_object=None,
                 list_of_tweets=None, filename_for_tweets=None, stopwords=None, print_verbose=False):
        """
        Initialize the twitter user. Must supply either screen_name, user_id, user_data_object,
                            list_of_tweets or filename_for_tweets
        :param screen_name: a user's screen_name
        :param user_id: a user's id
        :param api_hook: an OAuth1Service session... if you have one, this code will use it
                        in future calls you want to make to the Twitter API
        :param user_data_object: A user object that exists within a Tweet object; a rapid way to create
                        a TwitterUser without instantiating all the class objects, which is expensive
        :param list_of_tweets: A python list of tweets to use to instantiate the user
        :param filename_for_tweets: A filename (.json or .gz) giving the user's tweets
        :param stopwords: Any stopwords to be used to tokenize the user's tweets (defaults to twitter_dm standard stoplist)
        :param print_verbose: Should twitter_dm present verbose output?
        :return: twitter_dm.TwitterUser.TwitterUser
        """

        # Needs to be instantiated before anything else
        self.tweets = []

        if user_data_object:
            self.populate_user_data(user_data_object)
            return

        if stopwords is None:
            stopwords_stream = resource_stream('twitter_dm', 'data/stopwords.txt')
            self.stopwords = set([word.strip() for word in stopwords_stream.readlines()])
        else:
            self.stopwords = set([s for s in stopwords])

        # All of these are populated when you get a user's tweets from the API
        ##############

        self.replied_to = Counter()
        self.replied_to_sns = Counter()

        # Counter of number of times person has mentioned other users with these Twitter IDs
        self.mentioned = Counter()

        # Counter of number of times person has mentioned other users with these Twitter Screen Names
        # (same as above, except screen names instead of IDs)
        self.mentioned_sns = Counter()

        # Same as mentions, except for other users this person has retweeted
        self.retweeted = Counter()
        self.retweeted_sns = Counter()

        # Counter for hashtags used by this user
        self.hashtags = Counter()

        # Tokens Info
        self.tokens = Counter()

        # Tweets that were retweets
        self.retweeted_tweets = []

        ##############
        ##############


        # Friend IDs, Populated with populate_friends() method
        self.friend_ids = []

        # Follower IDs, populated with populate_followers() method
        self.follower_ids = []

        # Lists the user is a member of, populated with populate_lists_member_of() method
        self.lists_member_of = []

        # Lists the user owns, populated with populate_lists_owned() method
        self.lists_owned = []

        ##### User description features #####
        self.name = None
        self.description = None
        self.n_total_tweets = None
        self.creation_date = None
        self.location = None
        self.homepage = None
        self.utc_offset = None
        self.followers_count = -1
        self.following_count = -1
        self.lang = None
        self.times_listed = -1
        self.time_zone = None
        self.utc_offset = -1
        self.profile_img = None

        self.earliest_tweet_time = None
        self.latest_tweet_time = None

        ##############

        self.print_verbose = print_verbose

        if list_of_tweets is not None:
            # If you've passed in a list of tweets, then "hydrate" this user
            self.populate_tweets(list_of_tweets)
        elif filename_for_tweets is not None:
            # Or, give a file name (either .gz or a raw file w/ JSON) to load tweets from there
            self.populate_tweets_from_file(filename_for_tweets)
        elif user_data_object is not None:
            self.populate_user_data(user_data_object)
        else:
            # Otherwise, set up the user to be hydrated with future populate_* calls
            # SESSION INFO
            self.api_hook = api_hook

            if api_hook and not screen_name and not user_id:
                raise Exception('error', 'supply either screen name or user id')

            self.screen_name = screen_name
            # for backwards compatability, but move towards just "id" to mirror api
            self.user_id = user_id
            self.id = self.user_id
            # so I don't have to try to remember each time whether its an int or string
            self.id_int = int(self.id) if self.id else None
            self.id_str = str(self.id) if self.id else None

    def populate_tweets(self, tweets, convert_to_tweet=True, **kwargs):
        """
        Populates tweets from a list of python dictionary objects.
        Use populate_tweets_from_api to get if from the API
        :param tweets: list of python dictionaries (i.e. from json.loads())
        :param kwargs: keywords to pass to Tweet constructor
        :return:
        """

        if len(tweets) == 0:
            return

        i = 0

        if self.earliest_tweet_time is None:
            self.earliest_tweet_time = datetime.datetime.max
            self.latest_tweet_time = datetime.datetime.min

        for t in tweets:
            if convert_to_tweet:
                tweet = Tweet.Tweet(t, noise_tokens=self.stopwords, **kwargs)
            else:
                tweet = t
            self.tweets.append(tweet)

            if tweet.created_at and type(tweet.created_at) is not str and type(tweet.created_at) is not unicode:
                if tweet.created_at < self.earliest_tweet_time:
                    self.earliest_tweet_time = tweet.created_at
                if tweet.created_at > self.latest_tweet_time:
                    self.latest_tweet_time = tweet.created_at

            ##mentions
            for mention in tweet.mentions:
                self.mentioned[mention] += 1
            for mention_sn in tweet.mentions_sns:
                self.mentioned_sns[mention_sn] += 1

            ##replies
            if tweet.reply_to is not None:
                self.replied_to[tweet.reply_to] += 1
            if tweet.reply_to_sn is not None:
                self.replied_to_sns[tweet.reply_to_sn] += 1

            ##retweets
            if tweet.retweeted is not None:
                self.retweeted[tweet.retweeted] += 1
            if tweet.retweeted_sn is not None:
                self.retweeted_sns[tweet.retweeted_sn] += 1
            if tweet.retweeted_user_tweet_count > 0:
                self.retweeted_tweets.append(i)

            ##tokens and HTs
            if tweet.tokens:
                for term in tweet.tokens:
                    self.tokens[term] += 1
            for ht in tweet.hashtags:
                self.hashtags[ht] += 1
            i += 1

        # INFO ABOUT USER
        if convert_to_tweet:
            user_data = tweets[-1]['user']
            self.populate_user_data(user_data, do_parse_date=True)
        else:
            self.copy_user_data(tweets[-1].user)
        


    def copy_user_data(self, user_data):
        self.user_id = user_data.user_id
        self.id = self.user_id
        self.screen_name = user_data.screen_name
        self.name = user_data.name
        self.description = user_data.description
        self.n_total_tweets = user_data.n_total_tweets
        self.creation_date = user_data.creation_date
        self.location = user_data.location
        self.homepage = user_data.homepage
        self.times_listed = user_data.times_listed
        self.utc_offset = user_data.utc_offset
        self.followers_count = user_data.followers_count
        self.following_count = user_data.following_count
        self.lang = user_data.lang
        self.time_zone = user_data.time_zone
        self.utc_offset = user_data.utc_offset
        self.profile_img = user_data.profile_img
        self.verified = user_data.verified
        self.protected = user_data.protected

    def populate_user_data(self, user_data, do_parse_date=False):
        self.user_id = get_user_id_str(user_data)
        self.id = self.user_id
        self.screen_name = user_data.get('screen_name', None)
        self.name = user_data.get('name', None)
        self.description = user_data.get('description', None)
        self.n_total_tweets = user_data.get('statuses_count', None)
        if 'created_at' in user_data and do_parse_date:
            self.creation_date = parse_date(user_data['created_at'])
        self.creation_date = user_data.get('created_at', None)
        self.location = user_data.get('location', None)
        self.homepage = None
        if 'entities' in user_data and 'url' in user_data['entities'] and 'urls' in user_data['entities']['url']:
            self.homepage = user_data['entities']['url']['urls'][0]['expanded_url']
        self.times_listed = user_data.get('listed_count', -1)
        self.utc_offset = user_data.get('utc_offset', None)
        self.followers_count = user_data.get('followers_count', -1)
        self.following_count = user_data.get('friends_count', -1)
        self.lang = user_data.get('lang', '')
        self.time_zone = user_data.get("time_zone",'')
        self.utc_offset = user_data.get("utc_offset",-1)
        self.profile_img = user_data.get("profile_image_url_https",'')
        self.verified = user_data.get("verified",False)
        self.protecdted = user_data.get("protected",False)

    def gen_user_info_dict(self):
        if self.tweets:
            n_captured_tweets = len(self.tweets)
        else:
            n_captured_tweets = 0

        return {
            "user_id": self.user_id,
            "screen_name": self.screen_name,
            "name": self.name,
            "description": self.description,
            "n_total_tweets": self.n_total_tweets,
            "n_captured_tweets": n_captured_tweets,
            "creation_date": self.creation_date,
            "location": self.location,
            "homepage": self.homepage,
            "times_listed": self.times_listed,
            "utc_offset": self.utc_offset,
            "followers_count": self.followers_count,
            "following_count": self.following_count,
            "verified" : self.verified,
            "protected" : self.protected
        }

    def _get_file_name(self, json_output_directory, json_output_filename, is_gzip):
        out_fil_name = None
        if json_output_directory is not None or json_output_filename is not None:
            # if a file name is provided
            if json_output_filename is not None:
                is_gzip = is_gzip or json_output_filename.endswith(".gz")
                out_fil_name = json_output_filename

                # add the correct file endings
                if not (out_fil_name.endswith(".json") or out_fil_name.endswith(".gz")):
                    out_fil_name += ".json"
            else:
                if json_output_directory != '':
                    out_fil_name = os.path.join(json_output_directory, self.user_id + ".json")
                else:
                    out_fil_name = self.user_id + ".json"

            if is_gzip:
                if not out_fil_name.endswith(".gz"):
                    out_fil_name += ".gz"
        return out_fil_name

    def populate_tweets_from_api(self, json_output_directory=None,
                                 json_output_filename=None,
                                 sleep_var=True,
                                 is_gzip=True,
                                 populate_object_with_tweets=True,
                                 return_tweets= False,
                                 since_id=None):
        """
        Gets the last ~3200 tweets for the user from the Twitter REST API
        :param since_id:
        :param is_gzip:
        :param sleep_var:
        :param json_output_filename:
        """
        params = {
            'include_rts': 1,  # Include retweets
            'count': 200,  # 200 tweets
        }

        # get file to output to
        if json_output_filename and os.path.exists(json_output_filename):
            out_fil_name = json_output_filename
        else:
            out_fil_name = self._get_file_name(json_output_directory, json_output_filename, is_gzip)

        max_tw_id = None
        t_count = 0

        # If the file provided exists, then we need to find the last ID
        if out_fil_name and os.path.exists(out_fil_name):
            fil = gzip.open(out_fil_name) if out_fil_name.endswith(".gz") else io.open(out_fil_name)
            line = None
            for line in fil:
                t_count += 1
            if line:
                max_tw_id = json.loads(line)['id']

        # get since the last existing tweet if a since_id is given or we have existing tweets
        if since_id:
            params['since_id'] = since_id
        elif max_tw_id:
            params['since_id'] = max_tw_id

        # get the tweets from the API
        tweets_from_api = self.api_hook.get_with_max_id_for_user(
            'statuses/user_timeline.json',
            params,
            self.screen_name,
            self.user_id,
            sleep_var=sleep_var
        )

        if out_fil_name:
            tweets_from_api.sort(key = lambda x: parse_date(x['created_at']))
            if out_fil_name.endswith(".gz"):
                out_fil = gzip.open(out_fil_name, "ab")
                for tweet in tweets_from_api:
                    out_fil.write(json.dumps(tweet).strip().encode("utf8") + "\n")
            else:
                out_fil = io.open(out_fil_name, "a")
                for tweet in tweets_from_api:
                    out_fil.write(json.dumps(tweet).strip() + u"\n")
            out_fil.close()

        # populate the objects
        if populate_object_with_tweets:
            self.populate_tweets_from_file(out_fil_name)

        sig = self.screen_name if self.screen_name else self.user_id
        print t_count+len(tweets_from_api), ' total tweets for: ', sig , ' ', len(
            tweets_from_api), ' new tweets from API'

        if return_tweets:
            return tweets_from_api
        else:
            return out_fil_name, len(tweets_from_api)

    def populate_basic_info(self):
        params = {"include_entities": "false"}
        self.api_hook.get_user_params(params,self.screen_name,self.user_id)

        user_data = self.api_hook.get_from_url("users/lookup.json",params)
        self.populate_user_data(user_data[0])


    def populate_tweets_from_file(self, filename, **kwargs):
        """
        :param filename: Name of file that has the tweets
        :param kwargs: keywords to pass on to the Tweet constructor
        :return:
        """
        if filename.endswith(".gz"):
            reader = [z.decode("utf8") for z in gzip.open(filename).read().splitlines()]
        else:
            reader = codecs.open(filename, "r", "utf8")

        tweets = [json.loads(l) for l in reader]
        self.populate_tweets(tweets, **kwargs)

    def populate_lists_member_of(self, sleep_var=False, print_output=False):
        if self.times_listed > 0:
            lists = self.api_hook.get_with_cursor_for_user(
                "lists/memberships.json",
                "lists",
                self.screen_name,
                self.user_id,
                sleep_var=sleep_var)

            for l in lists:
                self.lists_member_of.append({'creating_user_name': l['user']['screen_name'],
                                             'creating_user_id': l['user']['id_str'],
                                             'created_at': parse_date(l['created_at']),
                                             'n_subscribers': l['subscriber_count'],
                                             'n_members': l['member_count'],
                                             'name': l['name'],
                                             'description': l['description'],
                                             'id': l['id_str'],
                                             'twitter_full_name': l['full_name']})
        if print_output:
            print('LISTS: ')
            for l in self.lists_member_of:
                print(l)

    def populate_lists_owned(self, sleep_var=True, print_output=False):
        self.lists_owned = self.api_hook.get_with_cursor_for_user(
            "lists/ownerships.json",
            "lists",
            self.screen_name,
            self.user_id,
            sleep_var=sleep_var,
            params={"count": 1000})
        if print_output:
            print('LISTS: ')
            for l in self.lists_owned:
                print(l)

    def populate_friends(self, sleep_var=True,print_output=False):
        self.friend_ids = self.api_hook.get_with_cursor_for_user(
            "friends/ids.json",
            "ids",
            self.screen_name,
            self.user_id,
            params={"count":5000},
            sleep_var=sleep_var)
        if print_output:
            print('NUM FRIENDS: ', len(self.friend_ids))

    def populate_followers(self, sleep_var=True,print_output=False):
        self.follower_ids = self.api_hook.get_with_cursor_for_user(
            "followers/ids.json",
            "ids",
            self.screen_name,
            self.user_id,
            params={"count":5000},
            sleep_var=sleep_var)
        if print_output:
            print('NUM FOLLOWERS: ', len(self.follower_ids))

    def counter_to_links(self, full_net, single_net, name, restriction_set):
        for k, v in single_net.iteritems():
            if restriction_set is None or k in restriction_set and k != self.screen_name:
                full_net.append([self.user_id, k, v, name])

    def get_ego_network(self, restrict_output_to_user_names=None):
        network = []
        self.counter_to_links(network, self.retweeted, "RT", restrict_output_to_user_names)
        self.counter_to_links(network, self.mentioned, "Mention", restrict_output_to_user_names)
        self.counter_to_links(network, self.replied_to, "Reply", restrict_output_to_user_names)
        return network

    def get_ego_network_actors(self):
        all_net = self.retweeted + self.mentioned + self.replied_to
        return [k for k in all_net.keys() if k != self.user_id]

    def write_counter(self, output, string_to_write, n_top, counter_data):
        output.write(u'\n {0}:'
                     '\n\tTOTAL UNIQUE: {1}'
                     '\n\tTop {2}: {3}'.
                     format(string_to_write,
                            len(counter_data),
                            n_top,
                            json.dumps(counter_data.most_common(n_top))))

    def __unicode__(self):
        output = StringIO.StringIO()
        output.write(u'USER')
        output.write(u'\n\tNAME: {0} ({1})'.format(self.screen_name, self.name))
        output.write(u'\n\tLOCATION: {0}'.format(self.location))
        output.write(u'\n\tDESCRIPTION: {0}'.format(self.description))
        output.write('\n\tNUM FRIENDS: {0}'.format(self.following_count))
        output.write('\n\tNUM_FOLLOWERS: {0}'.format(self.followers_count))
        output.write('\n\tTWEET COUNT: {0} (total {1})'.format(len(self.tweets), self.n_total_tweets))
        output.write('\n\tEARLIEST TWEET SEEN: {0}'.format(self.earliest_tweet_time))
        output.write('\n\tLATEST TWEET SEEN: {0}'.format(self.latest_tweet_time))
        output.write(
            '\n\tTOTAL OBSERVED DAYS ACTIVE: {0} days'.format((self.latest_tweet_time - self.earliest_tweet_time).days))

        if self.print_verbose:
            n_top = 15
            self.write_counter(output, 'Mentioned', n_top, self.mentioned)
            self.write_counter(output, 'Retweeted', n_top, self.retweeted)
            self.write_counter(output, 'Replied to', n_top, self.replied_to)
            self.write_counter(output, 'Hashtags', n_top, self.hashtags)
            # self.write_counter(output, '\n\tHashtags in RTs', n_top, self.retweeted_someone_else_hashtags)
            # self.write_counter(output, '\n\tHashtags in own tweets that were RTd', n_top, self.user_was_retweeted_hashtags)
            self.write_counter(output, 'Terms', n_top, self.tokens)
            # self.write_counter(output, '\n\tTerms in RTs', n_top, self.retweeted_someone_else_tokens)
            # self.write_counter(output, '\n\tTerms in own tweets that were RTd', n_top, self.user_was_retweeted_tokens)

            output.write('\nList info:')
            output.write('\n\t On {0} lists'.format((len(self.lists_member_of))))
            for l in self.lists_member_of:
                output.write(u'\n\t\t Name: {0} Member count: {1} Subscriber count: {2}'.
                             format(l['name'], l['n_members'], l['n_subscribers']))

        v = output.getvalue()
        return v


def get_user_id_str(user_data):
    if 'id_str' in user_data:
        return user_data['id_str']
    if 'id' in user_data:
        return str(user_data['id'])
    return None


def get_user_ids_and_sn_data_from_list(data, handles, is_sns, out_fil=None):
    print len(data)
    if len(data) < 100:
        user_data_chunked = [data]
    else:
        i = 0
        user_data_chunked = []
        while i < len(data):
            user_data_chunked.append(data[i:(i + 100)])
            i += 100

        user_data_chunked.append(data[i - 100:len(data)])

    if is_sns:
        str_to_get = "screen_name"
    else:
        str_to_get = "user_id"
    user_screenname_id_pairs = []

    i = 0
    for x in user_data_chunked:
        print i
        i += 1

        api_hook = handles[random.randint(0, len(handles) - 1)]
        user_data = api_hook.get_from_url("users/lookup.json", {str_to_get: ",".join(x), "include_entities": "false"})
        for u in user_data:
            data = [u['screen_name'], u['id_str'],
                    str(u['statuses_count']),
                    str(u['followers_count']),
                    str(u['friends_count']),
                    str(u['listed_count'])]
            user_screenname_id_pairs.append(data)
            if out_fil is not None:
                out_fil.write(tsn(data))

    return user_screenname_id_pairs
