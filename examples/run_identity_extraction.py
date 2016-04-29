"""
This script will run the identity extraction tool on a directory of json files (can be gzipped),
    a particular screen name or a particular (possibly gzipped) json file.

The tool uses a pretrained model that comes with twitter_dm.  If you want to train your own model,
    check out github.com/kennyjoseph/identity_extraction_pub

The script requires several things that are not included in the existing twitter_dm. You should run
the script in the install directory called install_dependencies_identity_extraction.sh, which will
hopefully install everything you need.
"""

import os
from twitter_dm.nlp.nlp_helpers import *
from twitter_dm.TwitterUser import TwitterUser
from twitter_dm.Tweet import Tweet
from twitter_dm.nlp.tweeboparser import *
from twitter_dm.identity_extraction.run_helpers import gen_conll_data_for_prediction
import ujson as json

from twitter_dm.TwitterUser import TwitterUser
from twitter_dm import dependency_parse_tweets
import subprocess
from glob import glob
from twitter_dm.identity_extraction.run_helpers import *
import argparse
import sys
from twitter_dm import TwitterApplicationHandler


### Parse command line arguments
parser = argparse.ArgumentParser(description='Extract identities from Twitter data')
parser.add_argument('--tweebo_parser_location',
                   help="""
                   Location of the TweeboParser head directory - make sure you have build the executable!
                   You can find TweeboParser at https://github.com/ikekonglp/TweeboParser.
                   If you ran install/install_dependencies_identity_extraction.sh, and you're running from
                    the examples directory, you shouldn't have to change this.""",
                   default="../install/TweeboParser")

parser.add_argument('--glove_data_location',
                   help="""
                   Location of the Glove data - run the script install_dependencies_identity_extraction.sh in
                   the install directory and then point this to the file glove.twitter.27B.50d.gensim_ready.txt.gz
                   If you ran install/install_dependencies_identity_extraction.sh and you're running from
                    the examples directory, you shouldn't have to change this.""",
                   default="../install/glove.twitter.27B.50d.gensim_ready.txt.gz")

parser.add_argument('--brown_data_location',
                   help="""
                   Location of the ARK Brown cluster data - run the script install_dependencies_identity_extraction.sh in
                   the install directory and then point this to the file 50mpaths2.
                   If you ran install/install_dependencies_identity_extraction.sh, and you're running from
                    the examples directory, you shouldn't have to change this.""",
                   default="../install/50mpaths2")


parser.add_argument('--rule_based_jar_location',
                   help="""
                   Location of the JAR that runs the rule-based model and PTB taggin -
                   run the script install_dependencies_identity_extraction.sh in
                   the install directory and then point this argument to the file rule_based_model.jar.
                   If you ran install/install_dependencies_identity_extraction.sh, and you're running this from
                    the examples directory, you shouldn't have to change this parameter.""",
                   default="../install/rule_based_model.jar")

parser.add_argument('--json_file_or_folder',
                   help="""
                   Path to (possibly gzipped) file of tweets to run identity extractor on, or path to a
                   folder of such files""")

parser.add_argument('--screen_name',
                   help="""Screen name to collect tweets for and run identity extractor on""",
                   default="_kenny_joseph")

parser.add_argument('--path_to_twitter_credentials_file',
                    help="""If you supply a screen name, you also ned to supply API credentials
                     so that we can go collect the tweets of that user. Check the README of twitter_dm
                     for how this file should be formatted and for how to create a new one if you've never done so""")

parser.add_argument('--output_directory',
                   help="""Directory to output results into""", default="./identity_model")

args = parser.parse_args()


##############
### SET UP
##############
OUTPUT_DIR =  os.path.abspath(args.output_directory)
print 'OUTPUT DIRECTORY: ', OUTPUT_DIR
mkdir_no_err(OUTPUT_DIR)
DP_OUTPUT_DIRECTORY = os.path.join(OUTPUT_DIR, "dp")
mkdir_no_err(DP_OUTPUT_DIRECTORY)
JSON_OUTPUT_DIRECTORY = os.path.join(OUTPUT_DIR, "json")
mkdir_no_err(JSON_OUTPUT_DIRECTORY)
RULE_MODEL_OUTPUT_DIRECTORY = os.path.join(OUTPUT_DIR, "ptb")
mkdir_no_err(RULE_MODEL_OUTPUT_DIRECTORY)
IDENTITY_OUTPUT_DIRECTORY =os.path.join(OUTPUT_DIR, "fin")
mkdir_no_err(IDENTITY_OUTPUT_DIRECTORY)

TWEEBOPARSER_LOC = os.path.abspath(args.tweebo_parser_location)
print 'TWEEBOPARSER LOCATED AT: ', TWEEBOPARSER_LOC

GENSIM_MODEL_LOCATION = args.glove_data_location
BROWN_CLUSTER_LOCATION = args.brown_data_location

print "GENSIM AT: ", GENSIM_MODEL_LOCATION
print 'BROWN CLUSTERS AT: ', BROWN_CLUSTER_LOCATION

RULE_BASED_JAR_LOC = os.path.abspath(args.rule_based_jar_location)
print 'RULE BASED JAR FILE AT: ', RULE_BASED_JAR_LOC

#############
### GET DATA
#############

if args.json_file_or_folder:
    if os.path.isdir(args.json_file_or_folder):
        print 'Running with json directory: ', args.json_file_or_folder
    else:
        print 'Running with json file: ', args.json_file_or_folder
elif args.screen_name:
    print 'Running with screen name: ', args.screen_name
    args.json_file_or_folder = os.path.join(OUTPUT_DIR,args.screen_name+".json.gz")
    if os.path.exists(args.json_file_or_folder):
        print "User's tweets already in the system at: ", args.json_file_or_folder
    else:
        print "Getting user's tweets and saving to: ", args.json_file_or_folder
        if not args.path_to_twitter_credentials_file:
            print "Can't do anything with a screen name without some API credentials, see the help for this script " \
                  "and this parameter!"
            sys.exit(-1)

        app_handler = TwitterApplicationHandler(pathToConfigFile=args.path_to_twitter_credentials_file)
        user = TwitterUser(screen_name=args.screen_name,
                           api_hook=app_handler.api_hooks[0])
        user.populate_tweets_from_api(json_output_filename=args.json_file_or_folder,sleep_var=False)

########
# load the models and the files
########

print 'LOADING MODEL'
identity_model,feature_names = get_identity_model_and_features()

word_vector_model, all_dictionaries, ark_clusters, sets, names = get_init_data(GENSIM_MODEL_LOCATION,
                                                                               BROWN_CLUSTER_LOCATION)
print 'MODEL HAS BEEN LOADED'

def gen_json_for_tweets_of_interest(input_filename, output_filename):
    """
    This function generates a cleaned json file so that the identity
    extraction only happens on "interesting" tweets.  Right now,
    interesting is defined as non-retweets that have >4 tokens. Feel free to redefine
    as you feel is suitable

    :param input_filename: input json file name (Can be gzipped)
    :param output_filename: cleaned output json filename
    :return:
    """
    tweets_to_write = []

    if not os.path.exists(output_filename):
        try:
            u = TwitterUser()
            u.populate_tweets_from_file(input_filename,store_json=True)
            tweets_to_keep = [t for t in u.tweets if not t.retweeted and len(t.tokens) > 4]
            tweets_to_write += tweets_to_keep
        except:
            print 'FAILED TO PARSE JSON FILE: ', input_filename

        print 'WRITING JSON'
        out_fil = gzip.open(output_filename, "wb")
        for tweet in tweets_to_write:
            out_fil.write(json.dumps(tweet.raw_json).strip().encode("utf8") + "\n")
        out_fil.close()



def gen_ptb(json_input_filename, ptb_output_filename):
    """
    This function runs the input file through the Java-based part of speech tagger
    and rule-based model described in the paper that was used to create the dictionary bootstraps

    :param input_filename: A (possibly cleaned, possibly gzipped) JSON file
    :param output_filename: The name of the output file
    :return:
    """

    print 'in ptb'
    if not os.path.exists(ptb_output_filename):
        print 'RUNNING JAVA RULE-BASED STUFF'
        try:
            subprocess.Popen("java -jar "
                         '{jar_location} {input_fil} {output_fil} 1 3'.format(
                                jar_location=RULE_BASED_JAR_LOC,
                                input_fil=json_input_filename,
                                output_fil=ptb_output_filename),
                             shell=True).wait()
        except:
            print 'FAILED JAVA STUFF'



def gen_dp(json_input_filename, dp_output_filename):
    """
    This function generates a dependency parse file (ending in dp) that will be used to create
     features for the identity extractor model. This process takes by far the longest of any
     process in this file. It calls out to a shell script that runs tweeboparser.

    :param json_input_filename: A (possibly cleaned, possibly gzipped) JSON file
    :param dp_output_filename: An output filename for the dependency parse
    :return:
    """

    reader = [z.decode("utf8") for z in gzip.open(json_input_filename).read().splitlines()]
    tweets_to_write = [Tweet(json.loads(l),do_tokenize=False) for l in reader]

    if not os.path.exists(dp_output_filename+".gz"):
        print 'DOING DP', dp_output_filename
        try:
            dp = dependency_parse_tweets(TWEEBOPARSER_LOC,tweets_to_write, dp_output_filename)
        except:
            print 'FAILED DP STUFF: ', dp_output_filename



def gen_predictions(json_input_file, ptb_input_file, dp_input_file, final_output_filename):
    """

    :param json_input_file:
    :param ptb_input_file:
    :param dp_input_file:
    :param final_output_filename:
    :return:
    """

    if os.path.exists(final_output_filename):
        print 'done already: ', final_output_filename
        return 'done'

    reader = [z.decode("utf8") for z in gzip.open(json_input_file).read().splitlines()]
    tweets_to_write = [Tweet(json.loads(l), do_tokenize=False) for l in reader]

    print 'getting prediction data', final_output_filename
    prediction_data = gen_conll_data_for_prediction(tweets_to_write,ptb_input_file, dp_input_file+".gz")
    print 'running prediction', final_output_filename
    preds = run_prediction(prediction_data, all_dictionaries,
                           ark_clusters, sets,names, feature_names,
                           word_vector_model, identity_model)

    outfil = gzip.open(final_output_filename, "wb")

    for k, row in preds.items():
        tweet = [x.get_super_conll_form() for x in row]
        outfil.write(("\n".join(tweet) + "\n\n").encode("utf8"))
    outfil.close()

files_to_run_on = [args.json_file_or_folder]\
                    if not os.path.isdir(args.json_file_or_folder) \
                    else glob(args.json_file_or_folder)

for json_input_name in files_to_run_on:
    basename = os.path.basename(json_input_name).replace(".json","").replace(".gz","")
    print 'running on file: ', json_input_name
    print '\t basename: ', basename

    print '\t cleaning json'
    clean_json_name = os.path.join(JSON_OUTPUT_DIRECTORY, basename+".json.gz")
    gen_json_for_tweets_of_interest(json_input_name,clean_json_name)

    print '\t running part of speech, rule based model'
    ptb_name = os.path.join(RULE_MODEL_OUTPUT_DIRECTORY,basename+".ptb.gz")
    gen_ptb(clean_json_name,ptb_name)

    print '\t running dependency parser'
    dp_name = os.path.join(DP_OUTPUT_DIRECTORY,basename+".dp")
    gen_dp(clean_json_name,dp_name)

    print '\t running identity model'
    final_output_name = os.path.join(IDENTITY_OUTPUT_DIRECTORY,basename+".txt.gz")
    gen_predictions(clean_json_name,ptb_name, dp_name,final_output_name)

    print '\t done with: ', basename, ' saved to: ', final_output_name