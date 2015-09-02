__author__ = 'kjoseph'


""" An example of how to do (parallelized) dependency parsing.
Still working on the tools to make the result easier to work with.
Note that you can get TweeboParser from the amazing ArkNLP guys:
ark.cs.cmu.edu/TweetNLP

Just make sure TWEEBOPARSER_LOC points to that directory and you should be good to go!
"""

from twitter_dm import dependency_parse_tweets
from twitter_dm import TwitterUser
from twitter_dm.utility.general_utils import mkdir_no_err
from glob import glob
from multiprocessing import Pool
import os

CPU_COUNT = 2
TWEEBOPARSER_LOC= 'PATH_TO_TWEEBO_PARSER'
DATA_DIR = "PATH_TO_DIRECTORY_OF_(GZIPPED)_JSON_FILES_WITH_TWEETS"



def do_dependency_parse(fil):
    u = TwitterUser()
    u.populate_tweets_from_file(fil,do_tokenize=False)
    out_file_name = fil.replace(".json","").replace(".gz","").replace("/json/","/dep_parse/")
    print out_file_name

    if len(u.tweets) == 0:
        os.utime(out_file_name)
        return 'empty, success'

    data = dependency_parse_tweets(TWEEBOPARSER_LOC,u.tweets,out_file_name)
    return 'completed'


mkdir_no_err(DATA_DIR.replace("json","dep_parse"))
pool = Pool(processes=CPU_COUNT)

#do_dependency_parse(glob(DATA_DIR+"/*")[0])
result = pool.map(do_dependency_parse, glob(DATA_DIR+"/*"))
