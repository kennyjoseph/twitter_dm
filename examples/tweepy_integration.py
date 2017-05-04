from __future__ import absolute_import, print_function

from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from twitter_dm import Tweet
import requests
import sys

consumer_key = "YOUR_CONSUMER_KEY_HERE"
consumer_secret = "YOUR_CONSUMER_SECRET_HERE"
access_token = "YOUR_ACCESS_TOKEN_HERE"
access_token_secret = "YOUR_ACCESS_TOKEN_SECRET_HERE"

user_set = set()
SAMPLE_SIZE = 100000
class BaseTweepyListener(StreamListener):
    def __init__(self):
        super(StreamListener, self).__init__()

    def on_data(self, data):
        try:
            t = Tweet(data, do_tokenize=False)

            if t.lang != 'en':
                return
            user_set.add(t.user.id)
        except:
            return True

        if len(user_set) % 1000 == 0:
            print(len(user_set))
        if len(user_set) == SAMPLE_SIZE:
            of = open("sampled_user_ids.txt","w")
            for u in user_set:
                of.write(str(u)+"\n")
            of.close()
            sys.exit(-1)

        return True

    def on_error(self, status):
        print(status)


if __name__ == '__main__':
    l = BaseTweepyListener()
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    while True:
        try:
            stream = Stream(auth, l)
            stream.filter(track=['clinton','trump','@realDonaldTrump','@HillaryClinton',
                                 'Hillary','#maga','#imwither','donald','#election2016'])
        except requests.packages.urllib3.exceptions.ProtocolError:
            pass
        except requests.packages.urllib3.exceptions.ReadTimeoutError:
            pass
