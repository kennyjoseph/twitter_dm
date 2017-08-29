import io
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from twitter_dm import Tweet
import requests
import sys
import gzip
from twitter_dm.utility.general_utils import Unbuffered, get_handles_from_filepath
import json

class BaseTweepyListener(StreamListener):
    def __init__(self, output_file):
        super(StreamListener, self).__init__()
        self.nt = 0
        self.output_file = output_file
        
    def on_data(self, data):
        if self.nt % 1000 == 0:
            print(self.nt)
        self.nt +=1 
        if data:
            try:
                self.output_file.write((data.strip()+u"\n").encode("utf8"))
            except:
                pass
        return True

    def on_error(self, status):
        print(status)



if len(sys.argv) != 4:
    print 'Usage: python tweepy_integration.py [path_to_cred_file] [output_filename] [keywords, separated by commas]'
    sys.exit(-1)

handles = get_handles_from_filepath(sys.argv[1])
output_file = Unbuffered(gzip.open(sys.argv[2],"wb"))
keywords = [x.strip() for x in sys.argv[3].split(",")]

print '\n\n\nbegin tracking: ', keywords

print " output to: ",  sys.argv[2]

handle = handles[0]

while True:

    auth = OAuthHandler(handle.consumer_key, handle.consumer_secret)
    auth.set_access_token(handle.access_token, handle.access_token_secret)

    try:
        stream = Stream(auth, BaseTweepyListener(output_file))
        stream.filter(track=['statue','unitetheright','march on google'])
    except requests.packages.urllib3.exceptions.ProtocolError:
        pass
    except requests.packages.urllib3.exceptions.ReadTimeoutError:
        pass
    except AttributeError:
        print 'strip error'
        pass
