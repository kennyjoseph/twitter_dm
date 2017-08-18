import io
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from twitter_dm import Tweet
import requests
import sys
import gzip

consumer_key = "ax8ZTDCTf1nllVyFs384lYHqE"
consumer_secret = "GA9NXowSo6hMQHdP0Un0aZK1qgck6BS6qDcDD5QfET08XMCM6j"
access_token = "2798401248-uTPiFgXDktgoXw40a85bzmpe106AX5kCc8zCFxd"
access_token_secret = "Yg4w06KeqQK02ucgaVX5iqX2ld5BEAE5QeEUgWbsvByua"

user_set = set()
SAMPLE_SIZE = 5000000
nt = 0
of = gzip.open(sys.argv[1],"wb")
class BaseTweepyListener(StreamListener):
    def __init__(self):
        super(StreamListener, self).__init__()
        self.nt = 0
        
    def on_data(self, data):
        if self.nt % 1000 == 0:
            print(self.nt)
        self.nt +=1 
        #try:
        #    t = Tweet(data, do_tokenize=False)

        #    if t.lang != 'en':
        #        return
        #    user_set.add(t.user.id)
        #except:
        #    return True

        #if len(user_set) % 1000 == 0:
        #    print(len(user_set))
        #if len(user_set) == SAMPLE_SIZE:
        #    of = open("sampled_user_ids.txt","w")
        #    for u in user_set:
        #        of.write(str(u)+"\n")
        #    of.close()
        #    sys.exit(-1)
        if data:
            try:
                of.write((data.strip()+u"\n").encode("utf8"))
            except:
                pass
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
            stream.filter(track=['statue','unitetheright','march on google'])
        except requests.packages.urllib3.exceptions.ProtocolError:
            pass
        except requests.packages.urllib3.exceptions.ReadTimeoutError:
            pass
