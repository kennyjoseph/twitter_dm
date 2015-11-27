__author__ = 'kennyjoseph'
import numpy as np
from evaluation import evaluate
from sklearn.feature_extraction.text import CountVectorizer
from functools import partial
from sklearn.linear_model import LogisticRegression
from features import *
import codecs
from collections import defaultdict
from twitter_dm.utility.tweet_utils import get_stopwords
from datetime import datetime
import os
import langid
from ..utility.general_utils import tab_stringify_newline as tsn
from ..utility.general_utils import read_grouped_by_newline_file

npcat = partial(np.concatenate, axis=1)
stopwords = get_stopwords()

def run_all_on_test_ids(fold,
                        test_ids,
                        word_vector_model,
                        features_from_conll,
                        dict_for_filter,
                        eval_params = [0.25,0.3,0.35,0.4,.45,.5,.6],
                        cutoff_params=[.0001],
                        use_filtered_params=[True],
                        datasets_to_use = ['full'],#'x','wv','x_wv','all_wv',
                        regularization_params = [.6]
                        ):

    return_info = []
    models = []
    predictions = []

    labels, features, obj_inds,\
    word_list, head_word_list,word_minus_one_list,\
    last_entity_word_list = configure_features_for_wordvectors_and_remove_twitterner(features_from_conll)


    train_inds,\
    test_inds,\
    stopword_train_inds,\
    stopword_test_inds = get_train_test_inds_w_filter(test_ids,dict_for_filter, obj_inds)


    w_vec = get_vector_rep_from_wordlist(word_list, word_vector_model, 50, True)
    head_vec = get_vector_rep_from_wordlist(head_word_list, word_vector_model, 50, True)
    last_vec = get_vector_rep_from_wordlist(last_entity_word_list, word_vector_model, 50, True)

    for cutoff_param in cutoff_params:

        count_vec = CountVectorizer(tokenizer=lambda x: x.split("|"),min_df=cutoff_param)
        X = count_vec.fit_transform(features).todense()
        y = np.array(labels)

        for use_filtered in use_filtered_params:
            to_use_train = train_inds
            to_use_test = test_inds
            to_use_stopword_inds = stopword_test_inds

            if not use_filtered:
                to_use_train = sorted(train_inds+stopword_train_inds)
                to_use_test = sorted(test_inds+stopword_test_inds)
                to_use_stopword_inds = []

            dataset_dict = {'x' : X,
                            'wv' : w_vec,
                            'x_wv' : npcat((X,w_vec)),
                            'all_wv': npcat((w_vec,head_vec,last_vec)),
                            'x_wv_ls' : npcat((X,w_vec,last_vec)),
                            'full' : npcat((X,w_vec,head_vec,last_vec)),
                            }

            for dataset_key in datasets_to_use:
                if dataset_key not in dataset_dict:
                    print 'KEY::: ', dataset_key, ' NOT IN DATASET OPTIONS, SKIPPING'
                    continue

                dataset = dataset_dict[dataset_key]

                pre_mod_out = [fold,cutoff_param,use_filtered,dataset_key]
                for c_val in regularization_params:

                    res,model,pred = run_and_output_model(dataset,y,
                                                          LogisticRegression(C=c_val,penalty='l1'),
                                                          obj_inds,
                                                          to_use_train,to_use_test,
                                                          eval_params,
                                                          pre_mod_out+[c_val],
                                                          to_use_stopword_inds)

                    return_info += res
                    models.append( model)
                    predictions.append(pred)
                print 'd ', fold
    return return_info, models, predictions




def run_and_output_model(X, y, model, obj_inds,
                         train_inds, test_inds,
                         eval_params, other_params,
                         stopword_test_inds):
    X_train = X[train_inds, :]
    y_train = y[train_inds]
    X_test = X[test_inds, :]
    y_test = y[test_inds]
    model = model.fit(X_train,y_train)

    if X_test.shape[0] == 0:
        return [], model, []

    predicted_prob = model.predict_proba(X_test)

    ret_dat = []

    stopword_test_inds_0 = []
    stopword_test_inds_1 = []

    for x in stopword_test_inds:
        if y[x] == 1:
            stopword_test_inds_1.append(x)
        else:
            stopword_test_inds_0.append(x)

    if len(stopword_test_inds):
        extra_tn = len(stopword_test_inds_0)
        extra_fn = len(stopword_test_inds_1)
        y_test = np.concatenate((y_test,np.array([0]*extra_tn),np.array([1]*extra_fn)),axis=0)
        predicted_prob = np.concatenate((predicted_prob,[[1,0]]*(extra_tn+extra_fn)),axis=0)
        test_inds = test_inds + stopword_test_inds_0 + stopword_test_inds_1

    for p in eval_params:
        o = evaluate(p, y_test, predicted_prob,obj_inds,test_inds,print_eval=False)
        ret_dat.append(other_params+o)

    return ret_dat, model, predicted_prob



def get_train_test_inds_w_filter(test_ids, dict_for_filter,obj_inds):
    train_inds = []
    test_inds = []
    stopword_train_inds = []
    stopword_test_inds = []
    for i, obj in enumerate(obj_inds):
        filter_out = should_filter(obj,dict_for_filter,lambda x: False)

        if obj.tweet_id in test_ids:
            if filter_out:
                stopword_test_inds.append(i)
            else:
                test_inds.append(i)
        else:
            if filter_out:
                stopword_train_inds.append(i)
            else:
                train_inds.append(i)

    return train_inds, test_inds, stopword_train_inds, stopword_test_inds


def write_out_predictions(outfile_name,test_data,obj_inds, test_inds, y, predicted_prob):
    pred_labs = defaultdict(dict)
    for i in range(len(y)):
        obj = obj_inds[test_inds[i]]
        if predicted_prob[i,1] >= .5:
            pred_labs[obj.tweet_id][obj.id] = "Identity"
        else:
            pred_labs[obj.tweet_id][obj.id] = "O"

    out_fil = codecs.open(outfile_name,"w","utf8")
    for k, row in test_data.items():
        i = 1
        for x in row:
            lab = pred_labs[k][i]
            out_fil.write(x + "\t" + lab  + "\n")
            i += 1
        out_fil.write("\n")
    out_fil.close()


def filter_user_tweets(user):
    """
    :param user:  A TwitterUser
    :return: A list of the tweets retained by the applied filter
    """
    return [t for t in user.tweets if
            (t.retweeted is None and len(t.urls) == 0 and 'http:' not in t.text
             and langid.classify(t.text)[0] == 'en')]


def gen_conll_data_for_prediction(tweets, ptb_filename, dp_filename):
    if not os.path.exists(dp_filename) or not os.path.exists(ptb_filename):
        print 'NO DP OR PTB::: ', dp_filename, ptb_filename
        return None

    penntreebank = {x[0] : x[1:] for x in read_grouped_by_newline_file(ptb_filename)}
    dependency_parse = {x[0] : x[1:] for x in read_grouped_by_newline_file(dp_filename)}

    data_to_return = []
    for tweet in tweets:

        data_for_tweet = []

        if str(tweet.id) not in penntreebank or str(tweet.id) not in dependency_parse:
            print 'tweet not in both files, continuing'
            continue

        ptb_for_tweet = penntreebank[str(tweet.id)]
        dp_for_tweet = dependency_parse[str(tweet.id)]

        if len(ptb_for_tweet) != len(dp_for_tweet):
            print 'tokenizations did not match, continuing'
            continue

        if ptb_for_tweet[0].split("\t")[2] != DependencyParseObject(dp_for_tweet[0]).text:
            print 'ahhhhh, weird stuff'
            continue

        for i, p in enumerate(dp_for_tweet):
            d = DependencyParseObject(tsn([p,tweet.id,tweet.user['id'],tweet.created_at.strftime("%m-%d-%y")],newline=False))
            # get java features
            spl_java = ptb_for_tweet[i].split("\t")
            java_id, penn_pos_tag,word = spl_java[:3]
            java_features = '' if len(spl_java) == 3 else spl_java[3]
            d.features += [x for x in java_features.split("|") if x != '']
            d.features.append("penn_treebank_pos="+penn_pos_tag)
            data_for_tweet.append(d)
        data_to_return.append(data_for_tweet)

    return data_to_return


def run_prediction(parse, all_dictionaries,
                   ark_clusters,sets,names, orig_feature_names,
                   word_vector_model, predict_model):
    """
    :param parse: the dependency parse from get_conll_data_for_prediction
    :param all_dictionaries: dictionaries used to create features
    :param ark_clusters: brown clusters information
    :param sets: the python sets that are acting as dictionaries
    :param names: the names of the python sets acting as dictionaries
    :param orig_feature_names: names of features in predict_model
    :param word_vector_model: the gensim word2vec model used to look up word representations
    :param predict_model: the model being used to make predictions
    :return: the same data as parse but appended with a label
    """

    pub_conll, dict_for_filter = get_all_features("",all_dictionaries,ark_clusters,sets, names, parse=parse)

    labels, features, obj_inds,\
    word_list, head_list, word_minus_one_list,\
    last_entity_word_list = configure_features_for_wordvectors_and_remove_twitterner(pub_conll)

    cv = CountVectorizer(tokenizer=lambda x: x.split("|"),vocabulary=orig_feature_names)
    X = cv.fit_transform(features)

    w_vec = get_vector_rep_from_wordlist(word_list, word_vector_model, 50,True)
    head_vec = get_vector_rep_from_wordlist(head_list, word_vector_model, 50,True)
    last_vec = get_vector_rep_from_wordlist(last_entity_word_list, word_vector_model,50,True)

    test_inds,a,  stopword_test_inds, b = get_train_test_inds_w_filter([],
                                                                       dict_for_filter,
                                                                       obj_inds)

    y = np.array(labels)
    D = np.concatenate((X.todense(),w_vec,head_vec,last_vec),axis=1)

    predicted_prob = predict_model.predict_proba(D[test_inds,:])

    stopword_test_inds_0 = []
    stopword_test_inds_1 = []

    for x in stopword_test_inds:
        if y[x] == 1:
            stopword_test_inds_1.append(x)
        else:
            stopword_test_inds_0.append(x)


    if len(stopword_test_inds):
        extra_tn = len(stopword_test_inds_0)
        extra_fn = len(stopword_test_inds_1)
        y = np.concatenate((y[test_inds],np.array([0]*extra_tn),np.array([1]*extra_fn)), axis=0)
        predicted_prob = np.concatenate((predicted_prob,[[1,0]]*(extra_tn+extra_fn)), axis=0)
        test_inds = test_inds + stopword_test_inds_0 + stopword_test_inds_1


    pred_labs = defaultdict(dict)
    for i in range(len(y)):
        obj = obj_inds[test_inds[i]]
        if predicted_prob[i,1] >= .5:
            pred_labs[obj.tweet_id][obj.id] = "Identity"
        else:
            pred_labs[obj.tweet_id][obj.id] = "O"

    test_data = {x[0].tweet_id : x for x in parse}
    return_data = {}
    for k, row in test_data.items():
        i = 1
        tweet = []
        for x in row:
            lab = pred_labs[k][i]
            x.label = lab
            tweet.append(x)
            i += 1
        return_data[k] =tweet

    return return_data
