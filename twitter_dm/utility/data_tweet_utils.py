"""
    This file contains utility functions to extract data
    from files and directories of tweets stored in .json files

    I hope to comment and provide more information soon.

"""
__author__ = 'kjoseph'

from twitter_dm import Tweet, TwitterUser
from twitter_dm.nlp import Tokenize
from collections import defaultdict, Counter
import ujson as json
import codecs, langid
import gzip


def parse_tweet_json_to_tweet_list(status):
    tweet_list = list()
    tweet_list.append(Tweet(status))
    new_status = status
    while tweet_list[-1].retweeted_user != "":
        new_status = new_status["retweeted_status"]
        tweet_list.append(Tweet(new_status))

    return tweet_list


def parse_tweet_json_file_to_dict(infile_path):
    import json
    skipped_lines = 0
    tweet_dict = {}
    with open(infile_path, "r") as infile:
        for line in infile:
            try:
                jsn = json.loads(line.strip())
                tweet_list = parse_tweet_json_to_tweet_list(jsn)

                for tweet in tweet_list:
                    if tweet.id_str not in tweet_dict:
                        tweet_dict[tweet.id_str] = tweet
                    else:
                        if tweet_dict[tweet.id_str].rt_count < tweet.rt_count:
                            tweet_dict[tweet.id_str].rt_count = tweet.rt_count
                        if tweet_dict[tweet.id_str].fv_max < tweet.fv_max:
                            tweet_dict[tweet.id_str].fv_max = tweet.fv_max

            except UnicodeDecodeError:
                # Couldn't parse line for some reason; ignore
                skipped_lines += 1

        print 'Skipped', skipped_lines
        return tweet_dict


def twitter_json_file_to_data_frame(infile_path, outfile_path):
    """Parses a file containing twitter JSON.
    Converts it to a multi-column, CSV file
    suitable for use with R.
    ID,DATE,TWEETER,OTHER_USER,HASHTAG,MENTION/RETWEET/SELF,RETWEET_COUNT,FAVORITE_COUNT"""
    import codecs
    tweet_dict = parse_tweet_json_file_to_dict(infile_path)
    with codecs.open(outfile_path, "w", "utf8") as outfile:
        outfile.write("id,date,tweeter,other_tweeter,hashtag,type,retweets,favorites\n")
        for id_str in tweet_dict:
                for line in tweet_dict[id_str].get_all_r_lines():
                    outfile.write(line+"\n")






def return_users_from_json_file(file_name,
                                user_id_field='id',
                                only_english=False,
                                min_tweet_count_for_user = 5,
                                verbose=True,
                                stopwords=None,
                                return_tweet_json=False):

    if file_name.endswith(".gz"):
        reader = [z.decode("utf8") for z in gzip.open(file_name).read().splitlines()]
    else:
        reader = codecs.open(file_name,"r","utf8")

    users = defaultdict(list)

    n_tweets = 0
    n_non_english = 0

    for line in reader:
        n_tweets+=1

        try:
            tweet = json.loads(line)
        except:
            print 'failed tweet'
            pass
        lang = tweet['lang'] if 'lang' in tweet else langid.classify(tweet['text'])[0]
        if not only_english or (only_english and lang == 'en'):
            # ignore the old tweets for now
            users[tweet['user'][user_id_field]].append(tweet)
        else:
            n_non_english += 1

    if not file_name.endswith(".gz"):
        reader.close()

    n_tweets = float(n_tweets)

    if n_tweets == 0 or (only_english and (n_tweets-n_non_english) == 0):
        return []

    good_users = [u for u in users.itervalues() if len(u) >= min_tweet_count_for_user]
    twitter_users = [TwitterUser(list_of_tweets=u,stopwords=stopwords) for u in good_users]

    if verbose:
        print '\tPercent non english tweets ignored:\t{:0.2f}'.format(n_non_english/n_tweets)
        print '\tNum used tweets:\t{0}'.format(n_tweets-n_non_english)
        print '\tN users pre min selection:\t', len(users)

        print '\tN users post min selection:\t', len(twitter_users)
        n_tweets_per_user = [len(u) for u in users.itervalues()]
        #print 'Tweet stats...min: %d max: %d median: %d mean: %d sd: %d' % \
        #(np.min(n_tweets_per_user),
        # np.max(n_tweets_per_user),
        # np.median(n_tweets_per_user),
        # np.mean(n_tweets_per_user),
        # np.std(n_tweets_per_user))


    if not return_tweet_json:
        return twitter_users

    tweet_dict = {}
    if return_tweet_json:
        for u in good_users:
            for t in u:
                tweet_dict[t['id']] = t
    return twitter_users, tweet_dict




def run_tweet_through_dictionaries(tweet, dictionaries, n_grams_to_use):
    return run_text_through_dictionaries(tweet.tokens,dictionaries,n_grams_to_use)



def run_text_through_dictionaries(tokens, dictionaries, n_grams_to_use):
    # split into grams. eventually, probably use
    # Microsoft's seg. algorithm
    gram_counter_array = []
    for n_g in range(n_grams_to_use,0, -1):
        gram_counter_array.append(Counter(Tokenize.getNGrams(tokens,n_g)))
    gram_counter_array_len = len(gram_counter_array)
    one_grams = gram_counter_array[gram_counter_array_len-1]

    # print '\n\nTWEET: ', tweet.text

    # print 'ONE GRAMS: ', one_grams
    # terms that were mapped to
    new_terms = []
    terms_replaced = []

    # for all N
    for grams in gram_counter_array :
        # for each dictionary
        for k,dictionary in dictionaries:
            # items we find in this dictionary
            to_rem = []
            # for this set of n-grams
            for g in grams.elements():
                replacement_text = dictionary.get_entities_for_text(g)
                # if we found it in the lookup, remove from 2grams and 1 grams, add to terms
                if replacement_text is not None:
                    # print g,replacement_text,k
                    # for now, just append first thing it maps too.
                    # eventually, an algorithm goes here, because this is bad
                    # new_terms.append(list(replacement_text)[0]+"%%" + k)
                    new_terms.append(list(replacement_text)[0])
                    terms_replaced.append(g)
                    to_rem.append(g)

            # because our dictionaries are ordered, we now want to remove to avoid mappings
            # in later dictionaries
            for term_to_remove in to_rem:
                gram_remove(gram_counter_array_len, gram_counter_array, term_to_remove)

    return new_terms, one_grams, terms_replaced

def gram_remove(gram_counter_array_len, gram_counter_array, term_to_remove):
    # by construction all grams are space separated
    term_spl = term_to_remove.split(" ")
    # length of term
    term_len = len(term_spl)

    # for a one gram, we only want to work with the last elt in gram array
    # for a two gram, the last two, etc
    for gram_ind in range(gram_counter_array_len-term_len, gram_counter_array_len):
        # get this gram counter
        grams = gram_counter_array[gram_ind]
        # the size of the array is the inverse of the position in the counter array
        gram_size = gram_counter_array_len-gram_ind
        # for each split of length gram_len
        for spl_iter in range(0,term_len-gram_size+1):
            grams[" ".join(term_spl[spl_iter:(spl_iter+gram_size)])] -= 1