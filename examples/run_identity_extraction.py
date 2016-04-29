"""
This script will run the identity extraction tool on a directory of json files (can be gzipped),
    a particular screen name or a particular (possibly gzipped) json file.

The tool uses a pretrained model that comes with twitter_dm.  If you want to train your own model,
    check out github.com/kennyjoseph/identity_extraction_pub

The script requires
"""

__author__ = 'kennyjoseph'
import os
from twitter_dm.nlp.nlp_helpers import *
import codecs
from twitter_dm.TwitterUser import TwitterUser
from twitter_dm.Tweet import Tweet
from twitter_dm.nlp.tweeboparser import *
from twitter_dm.identity_extraction.run_helpers import gen_conll_data_for_prediction
import ujson as json
import joblib

## MAKE SURE YOU RETRAIN THE IDENTITY MODEL FIRST USING train_identity_model.py
from twitter_dm.TwitterUser import TwitterUser
from twitter_dm import dependency_parse_tweets
import subprocess
from multiprocessing import Pool
import numpy as np
from glob import glob
from copy import copy
from twitter_dm.identity_extraction.run_helpers import *
identity_model = joblib.load("trained_identity_model.p")
feature_names = joblib.load("feature_names.p")

from twitter_dm.utility.general_utils import tab_stringify_newline as tsn
# do a simple unigram search with an expanded token set using get_alternate_wordforms in nlp_helpers

DATA_DIR = "../../data/ferg_geo_data/"

UIDS_TO_USE = [x.strip() for x in open(os.path.join(DATA_DIR,"recent/good_uids.txt"))]
JSON_INPUT_DIRECTORY = os.path.join(DATA_DIR,"geotagged_combined_json/")

# This needs to be a full path
DP_OUTPUT_DIRECTORY = "/usr1/kjoseph/thesis_work/lcss_study/data/ferg_geo_data/recent/dp/"
JSON_OUTPUT_DIRECTORY = os.path.join(DATA_DIR,"recent/json")
RULE_MODEL_OUTPUT_DIRECTORY = os.path.join(DATA_DIR,"recent/ptb")
IDENTITY_OUTPUT_DIRECTORY =os.path.join(DATA_DIR,"recent/fin")
IDENTITY_LIST_FN = "../../data/identity_data/final_identities_list.txt"
# this needs to be a full path, path to TweeboParser
TWEEBOPARSER_LOC = "/usr1/kjoseph/TweeboParser"
RULE_BASED_JAR_LOC = "../../java/rule_based_model.jar"


print 'getting data'
GENSIM_MODEL_LOCATION = "../../../identity_extraction/python/gensim_model/glove_twitter_50_raw_model.txt.gz"
BROWN_CLUSTER_LOCATION = "../../../identity_extraction/python/processed_data/50mpaths2"
DICTIONARIES_LOCATION = "../../../identity_extraction/python/dictionaries/*/*"
BOOTSTRAPPED_DICTIONARY_LOCATION = "../../../identity_extraction/python/processed_data/twitter_supervised_results.tsv"
word_vector_model, all_dictionaries, ark_clusters, sets, names = get_init_data(GENSIM_MODEL_LOCATION,
                                                                               BROWN_CLUSTER_LOCATION,
                                                                               DICTIONARIES_LOCATION,
                                                                               BOOTSTRAPPED_DICTIONARY_LOCATION)


def gen_json_for_tweets_of_interest(data, identity_list):
    of_id, uid_list = data
    json_of_name = os.path.join(JSON_OUTPUT_DIRECTORY,str(of_id)+".json.gz")

    print 'inp: ', json_of_name, len(uid_list), uid_list[0:2]
    tweets_to_write = []

    if not os.path.exists(json_of_name):
        for i, uid in enumerate(uid_list):
            if i % 25 == 0:
                print i, len(tweets_to_write)
            try:
                u = TwitterUser()
                u.populate_tweets_from_file(os.path.join(JSON_INPUT_DIRECTORY,uid+".json.gz"),store_json=True)
                tweets_to_keep = []
                for t in u.tweets:
                    if not t.retweeted and len(t.tokens) > 4:
                        expanded_token_set = copy(t.tokens)
                        for token in t.tokens:
                            expanded_token_set += get_alternate_wordforms(token)
                        if len(set(expanded_token_set) & identity_list):
                            tweets_to_keep.append(t)
                tweets_to_write += tweets_to_keep
            except:
                print 'FAILED JSON FOR USER: ', uid

        print 'WRITING JSON'
        out_fil = gzip.open(json_of_name, "wb")
        for tweet in tweets_to_write:
            out_fil.write(json.dumps(tweet.raw_json).strip().encode("utf8") + "\n")
        out_fil.close()

def gen_ptb(data):
    of_id, uid_list = data
    json_of_name = os.path.join(JSON_OUTPUT_DIRECTORY, str(of_id)+".json.gz")
    ptb_of_name = os.path.join(RULE_MODEL_OUTPUT_DIRECTORY, str(of_id)+".ptb.gz")

    print 'in ptb'
    if not os.path.exists(ptb_of_name):
        print 'RUNNING JAVA RULE-BASED STUFF'
        try:
            subprocess.Popen("java -jar "
                         '{jar_location} {input_fil} {output_fil} 1 3'.format(
                                jar_location=RULE_BASED_JAR_LOC,
                                input_fil=json_of_name,
                                output_fil=ptb_of_name),
                             shell=True).wait()
        except:
            print 'FAILED JAVA STUFF'

def gen_dp(data):
    of_id, uid_list = data
    json_of_name = os.path.join(JSON_OUTPUT_DIRECTORY,str(of_id)+".json.gz")
    dp_of_name = os.path.join(DP_OUTPUT_DIRECTORY,str(of_id)+".dp")

    reader = [z.decode("utf8") for z in gzip.open(json_of_name).read().splitlines()]
    tweets_to_write = [Tweet(json.loads(l),do_tokenize=False) for l in reader]

    if not os.path.exists(dp_of_name+".gz"):
        print 'DOING DP', dp_of_name
        try:
            dp = dependency_parse_tweets(TWEEBOPARSER_LOC,tweets_to_write, dp_of_name)
        except:
            print 'FAILED DP STUFF: ', dp_of_name

def gen_predictions(data):
        of_id, uid_list = data
        json_of_name = os.path.join(JSON_OUTPUT_DIRECTORY,str(of_id)+".json.gz")
        ptb_of_name = os.path.join(RULE_MODEL_OUTPUT_DIRECTORY, str(of_id)+".ptb.gz")
        dp_of_name = os.path.join(DP_OUTPUT_DIRECTORY,str(of_id)+".dp")
        final_output_name = os.path.join(IDENTITY_OUTPUT_DIRECTORY,str(of_id)+".txt.gz")

        if os.path.exists(final_output_name):
            print 'done already: ', final_output_name
            return 'done'

        reader = [z.decode("utf8") for z in gzip.open(json_of_name).read().splitlines()]
        tweets_to_write = [Tweet(json.loads(l),do_tokenize=False) for l in reader]

    #try:
        print 'getting prediction data', final_output_name
        prediction_data = gen_conll_data_for_prediction(tweets_to_write,ptb_of_name, dp_of_name+".gz")
        print 'running prediction', final_output_name
        preds = run_prediction(prediction_data, all_dictionaries,
                       ark_clusters, sets,names, feature_names,
                       word_vector_model, identity_model)

        outfil = gzip.open(final_output_name, "wb")
        i = 0
        for k, row in preds.items():
            tweet_has_identity = False
            tweet = []
            for x in row:
                lab = x.label
                if lab != 'O':
                    tweet_has_identity = True
                tweet.append(x.get_super_conll_form())
            if tweet_has_identity:
                i += 1
                outfil.write(("\n".join(tweet) + "\n\n").encode("utf8"))
        outfil.close()
    #except:
    #    print 'FAILED PREDICTIONS!!!', final_output_name


def get_identity_list():
    identity_set = {x.strip().lower() for x in open(IDENTITY_LIST_FN)}
    identity_list = set()
    for x in identity_set:
        identity_list |= set(x.split(" "))

    print len(identity_list)
    return identity_list

from functools import partial

identity_list = get_identity_list()

print 'N UIDS: ', len(UIDS_TO_USE)
data_chunks = np.array_split(UIDS_TO_USE, 200)
print 'LEN PER CHUNK: ', len(data_chunks[0])

#pool = Pool(60)

partial_get_tweets = partial(gen_json_for_tweets_of_interest, identity_list=identity_list)

data = list(enumerate(data_chunks))
print 'len dat: ', len(data)
#json_res = pool.map(partial_get_tweets,data)
#pool.close()
#pool = Pool(40)
#print 'len dat: ', len(data)
#ptb_res = pool.map(gen_ptb,data)
#pool.close()
#pool = Pool(25)
#dp_res = pool.map(gen_dp,data)
#pool.close()

pool = Pool(11)
pool.map(gen_predictions,data)
pool.close()
#gen_predictions([107,[]])
#for d in data:
#    gen_predictions(d)
