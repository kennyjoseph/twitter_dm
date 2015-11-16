__author__ = 'kennyjoseph'

import numpy as np
import pandas as pd
from ..utility.general_utils import read_grouped_by_newline_file
from dependency_parse_object import DependencyParseObject
import random

from sklearn.metrics import auc, roc_curve

def get_tp_fp_count_from_positive_predictions(data):
    tp = np.count_nonzero(data)
    return tp, data.shape[0]-tp

def compute_confusion_matrix(x,y):
    ct = pd.crosstab(x,y)

    tn = ct.iloc[0,0]
    fn = ct.iloc[0,1]
    if ct.shape[0] == 1:
        fp = 0
        tp = 0
    else:
        fp = ct.iloc[1,0]
        tp = ct.iloc[1,1]

    f1 = compute_f1(tp,fp,fn)
    return tn, fn, fp, tp, f1


def compute_f1(tp,fp,fn):
    return 2.*(tp)/(2.*tp+fn+fp)


def evaluate(v, y_test, predicted_prob, obj_inds, test_inds = None,
             print_eval=True, print_pos=False, print_neg=False):

    # test model
    predicted_positives = y_test[np.where(predicted_prob[:,1] > v)[0]]
    tp, fp = get_tp_fp_count_from_positive_predictions(predicted_positives)

    predicted_negatives = y_test[np.where(predicted_prob[:,1] <= v)[0]]
    fn = np.count_nonzero(predicted_negatives)
    tn = len(predicted_negatives)-fn

    f1 = compute_f1(tp,fp,fn)
    fpr, tpr, thresholds = roc_curve(y_test,predicted_prob[:,1])
    auc_val = auc(fpr,tpr)

    if not (tp+fn):
        recall =0
    else:
        recall = tp/float(tp+fn)

    prec = tp/float(predicted_positives.shape[0]) if predicted_positives.shape[0] != 0 else 0

    if print_eval:
        print f1, prec, recall
        print tp, fn
        print fp, tn

    if print_pos or print_neg:
        #evaluate model
        false_negs = []
        false_pos = []
        for i, y_test_val in enumerate(y_test):
            ind = i if not test_inds else test_inds[i]
            if (predicted_prob[i,1] < v and y_test_val == 1):
                false_negs.append([str(predicted_prob[i,1]), obj_inds[ind].text, obj_inds[ind].postag, str(ind), obj_inds[ind].tweet_id])
            if (predicted_prob[i,1] >= v and y_test_val == 0):
                false_pos.append([str(predicted_prob[i,1]), obj_inds[ind].text, obj_inds[ind].postag, str(ind), obj_inds[ind].tweet_id])

        if print_neg:
            print 'FALSE NEGS:'
            for i in false_negs:
                print '\t', "  ".join(i)
        if print_pos:
            print 'FALSE POS:'
            for i in false_pos:
                print '\t', "  ".join(i)

    return [v,tp,fn,fp,tn,prec,recall,f1, auc_val]



def get_test_ids(conll_filename, random_seed, n_rand_non_reply, n_rand_reply):
    dat = read_grouped_by_newline_file(conll_filename)

    rand_msg = []
    rand_reply = []
    others = []
    random.seed(random_seed)

    for row in dat:
        obj = DependencyParseObject(row[0])
        if obj.dataset == 'random':
            if obj.is_reply =='reply':
                rand_reply.append(obj.tweet_id)
            else:
                rand_msg.append(obj.tweet_id)
        else:
            others.append(obj.tweet_id)

    random.shuffle(rand_msg)
    random.shuffle(rand_reply)

    if n_rand_reply == -1:
        return rand_msg + rand_reply

    return rand_msg[:n_rand_non_reply] + rand_reply[:n_rand_reply]


