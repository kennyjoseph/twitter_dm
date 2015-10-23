__author__ = 'kennyjoseph'
from math import log

import pandas as pd
from dependency_parse_object import DependencyParseObject
from twitter_dm.utility.tweet_utils import get_stopwords
from RitterDictionaries import Dictionaries
import codecs
from util import *
from dependency_parse_handlers import *

######################################################################################################
######################################################################################################
######################################################################################################
#################################### CONLL BASED FEATURES
######################################################################################################
######################################################################################################
######################################################################################################

def get_init_data(model_file, ark_file, dict_filepath, twit_dict_file):
    from gensim.models.word2vec import Word2Vec
    model = Word2Vec.load_word2vec_format(model_file, binary=False)
    ark_clusters = get_ark_clusters(ark_file)
    all_dictionaries = Dictionaries(dict_filepath)
    twit_sets = []
    stopwords = get_stopwords()
    tw_distant_supervision_identity_dat = get_twitter_distant_supervision_identity_dat(twit_dict_file)

    for v in [10, 100, 1000, 10000,50000]:
        twit_id = set(tw_distant_supervision_identity_dat[
                      (tw_distant_supervision_identity_dat.tot > v)].term.values)
        twit_id = {t for t in twit_id if t not in stopwords and t.replace(" person","") not in stopwords}
        twit_sets.append([twit_id,"twit_identities_"+str(v)])

    twit_sets.append([EXPERT_NON_IDENTITIES,"expert_non"])
    twit_sets.append([stopwords,"stopword"])

    return model, all_dictionaries, ark_clusters, [t[0] for t in twit_sets],[t[1] for t in twit_sets]



def get_ark_clusters(filename= "processed_data/6mpaths.tsv"):
    ark_word_clusters = {}
    with codecs.open(filename,"r","utf8") as f:
        for row in f:
            row = row.strip().split("\t")
            if len(row) == 3:
                ark_word_clusters[row[1]] = [row[0],row[2]]
    return ark_word_clusters


def get_all_features(filename,
                     dictionaries,
                     ark_word_clusters,
                     sets,
                     set_names,
                     parse = None):

    features_to_return = {}

    if parse:
        dependency_parses = parse
    else:
        data = read_grouped_by_newline_file(filename)
        dependency_parses = []
        for x in data:
            dependency_parses.append([DependencyParseObject(o) for o in x])

    dictionary_based_features = look_in_dict(dependency_parses,dictionaries,sets,set_names)

    dependency_parse_features = get_dependency_parse_features(dependency_parses)

    for n, dependency_parse_objects in enumerate(dependency_parses):
        features_to_return[dependency_parse_objects[0].tweet_id] = []

        for i, o in enumerate(dependency_parse_objects):

            features_for_obj = list(get_basic_features(dependency_parse_objects,i))
            if ark_word_clusters and o.text.lower() in ark_word_clusters:
                features_for_obj.append( 'ark_clust_tot:'+ark_word_clusters[o.text.lower()][0])

            features_for_obj += dependency_parse_features[o.tweet_id][o.id-1]
            features_for_obj += list(dictionary_based_features[o.tweet_id][o.id-1])

            if o.id != 1:
                features_for_obj += ["w-1:dict:"+x for x in dictionary_based_features[o.tweet_id][o.id-2]]
            if o.id < (len(dependency_parse_objects)-1):
                features_for_obj += ["w+1:dict:"+x for x in dictionary_based_features[o.tweet_id][o.id]]

            features_to_return[o.tweet_id].append([o,features_for_obj])

    return features_to_return, dictionary_based_features


def get_dictionary_features(filename,
                            dictionary_location,
                            twitter_distance_supervision_file_location,
                            twitter_cutoffs):

    twit_sets = []
    stopwords = get_stopwords()
    if twitter_distance_supervision_file_location:
        tw_distant_supervision_identity_dat = get_twitter_distant_supervision_identity_dat(
                                                                    twitter_distance_supervision_file_location)


        for v in twitter_cutoffs:
            twit_id = set(tw_distant_supervision_identity_dat[
                          (tw_distant_supervision_identity_dat.tot > v)].term.values)
            twit_id = {t for t in twit_id if t not in stopwords and t.replace(" person","") not in stopwords}
            twit_sets.append([twit_id,"twit_identities_"+str(v)])


    twit_sets.append([EXPERT_NON_IDENTITIES,"expert_non"])
    twit_sets.append([stopwords,"stopword"])

    all_dicts = Dictionaries(dictionary_location)
    return look_in_dict(filename,all_dicts,[t[0] for t in twit_sets], [t[1] for t in twit_sets])


def get_basic_features(sentence, sentence_loc):

    obj = sentence[sentence_loc]

    feats = obj.word_features(False)

    if sentence_loc > 0:
        prior = sentence[sentence_loc-1]
        for x in prior.word_features(True):
            feats.append("word-1:" + x)

    if sentence_loc + 1 < len(sentence):
        post = sentence[sentence_loc+1]
        for x in post.word_features(True):
            feats.append("word+1:" + x)

    if sentence_loc + 2 < len(sentence):
       post = sentence[sentence_loc+2]
       feats.append("word+2:POS:"+post.postag)
    if sentence_loc - 2 >= 0:
       post = sentence[sentence_loc-2]
       feats.append("word-2:POS:"+post.postag)

    for f in feats:
        yield f


def configure_features_for_wordvectors_and_remove_twitterner(final_features):
    labels = []
    features = []
    obj_inds = []
    word_list = []
    head_word_list = []
    word_minus_one_list = []
    last_entity_word_list = []

    for f, v in final_features.iteritems():
        for i, v_enum in enumerate(v):
            obj, feat_set = v_enum
            labels.append(1 if 'Identity' in obj.label else 0)
            features.append('|'.join([z for z in feat_set if
                                     'word_low' not in z
                                     and 'word_last_word_in_entity:' not in z
                                     and 'twitterner' not in z
                                     and 'head_word:' not in z
                                     ]))

            found_head_1 = False
            found_minus_1 = False
            found_last = False
            for f in feat_set:
                if f.startswith("word_low:"):
                    word_list.append(remove_emoji(f.replace("word_low:","")))
                elif f.startswith("head_word:"):
                    head_word_list.append(remove_emoji(f.replace("head_word:","")))
                    found_head_1 = True
                elif f.startswith("word-1:word_low:"):
                    word_minus_one_list.append(remove_emoji(f.replace("word-1:word_low:","")))
                    found_minus_1 = True
                elif f.startswith("word_last_word_in_entity:"):
                    last_entity_word_list.append(remove_emoji(f.replace("word_last_word_in_entity:","")))
                    found_last = True
            if not found_head_1:
                head_word_list.append("<END>")
            if not found_minus_1:
                word_minus_one_list.append("<START>")
            if not found_last:
                last_entity_word_list.append("<<LAST>>")

            obj_inds.append(obj)

    return [labels, features, obj_inds,
            word_list, head_word_list, word_minus_one_list,
            last_entity_word_list]




def get_dependency_parse_features(dep_parses):
    features_dict = {}

    for dep_objs in dep_parses:

        features = defaultdict(list)

        for dp_obj in dep_objs:
            if dp_obj.head > 0:
                features[dp_obj.id-1].append("head_word:"+dep_objs[dp_obj.head-1].text)

        parse_out, term_map, map_to_head, non_terms = get_parse(dep_objs)
        entities, proper_nouns, entity_ids, proper_ids = get_entities_from_parse(term_map)

        for i, e in enumerate(entities):
            e = remove_emoji(e)

            if '@' in e or ('#' in e and len(e.split(" ")) == 1):
                continue

            atleast_one_noun = False
            for eid in entity_ids[i]:
                if dep_objs[eid-1].postag in ['N','^','A']:
                    atleast_one_noun = True
                    break
            if not atleast_one_noun:
                continue

            last_obj = dep_objs[entity_ids[i][-1]-1]
            features[entity_ids[i][-1]-1].append('last_word_in_entity')

            for fid in entity_ids[i][:-1]:
                features[fid-1].append('not_last_word_in_entity')
                features[fid-1].append('word_last_word_in_entity:'+last_obj.text)

            features[entity_ids[i][-1]-1].append('word_last_word_in_entity:'+last_obj.text)

            #for id in entity_ids[i]:
            #        features[id-1].append('solid_entity')

        for i, e in enumerate(proper_nouns):
            for id in proper_ids[i]:
                features[id-1].append('proper_noun')

        features_dict[dep_objs[0].tweet_id] = features
    return features_dict


######################################################################################################
######################################################################################################
######################################################################################################
#################################### WORD VECTOR FEATURES
######################################################################################################
######################################################################################################
######################################################################################################


def get_vector_rep_from_wordlist(word_list, model, size, clean_vector_first=False):
    dat = np.zeros((len(word_list),size))
    for i,w in enumerate(word_list):
        w = w.lower()
        if not len(w):
            continue
        first_char = w[0]
        if clean_vector_first:
            w = get_cleaned_text(w)
        if w.endswith("'s"):
            w = w[:-2]
        elif w.endswith("'"):
            w = w[:-1]
        if w in model.vocab:
            dat[i,:] = model.syn0norm[model.vocab[w].index]
        elif first_char == "@":
            if w in model.vocab:
                dat[i,:] = model.syn0norm[model.vocab[w[1:]].index]
            else:
                dat[i, :] = model.syn0norm[model.vocab["<user>"].index]
        elif first_char == "#":
            if w in model.vocab:
                dat[i,:] = model.syn0norm[model.vocab[w[1:]].index]
            else:
                dat[i, :] = model.syn0norm[model.vocab["<hashtag>"].index]
        elif w.split("'")[0] in model.vocab:
            if w.split("'")[1] in model.vocab:
                dat[i,:] = (model.syn0norm[model.vocab[w.split("'")[0]].index] +
                                model.syn0norm[model.vocab[w.split("'")[1]].index])/2
            else:
                dat[i,:] = model.syn0norm[model.vocab[w.split("'")[0]].index]
    return dat



######################################################################################################
######################################################################################################
######################################################################################################
#################################### DICTIONARY FEATURES
######################################################################################################
######################################################################################################
######################################################################################################


def get_twitter_distant_supervision_identity_dat(filename):
    stopwords = get_stopwords()
    identity_dat = pd.DataFrame.from_csv(filename,sep='\t',header=None,encoding="utf8").reset_index()
    identity_dat.columns = ['rule','term','count']
    identity_dat.term = identity_dat.term.apply(get_cleaned_text)
    identity_dat = identity_dat[identity_dat.term != '']
    identity_dat = identity_dat[identity_dat.term != ' person']
    identity_dat = identity_dat[identity_dat.term != 'person']
    grouped_data = identity_dat.groupby(["term","rule"]).sum().reset_index()
    identity_dat = grouped_data.pivot_table(values='count',
                                                index='term',columns='rule',
                                                fill_value=0)\
                                    .sort(inplace=False,columns='i',ascending=False)\
                                    .reset_index()
    identity_dat['tot'] = identity_dat.i + identity_dat.y + identity_dat.h + identity_dat.s + identity_dat.p
    identity_dat.sort("tot",inplace=True,ascending=False)
    identity_dat = identity_dat[identity_dat.term.apply(lambda x: not x in stopwords and not x.replace(" person","") in stopwords)]
    return identity_dat.reset_index()



def should_filter(o, dictionary_data, custom_filter):
    is_in_identities_in_dict = False
    is_stopword = False

    if (o.id-1) in dictionary_data[o.tweet_id]:
        for x in dictionary_data[o.tweet_id][o.id-1]:
            is_in_identities_in_dict |= 'identities' in x
            is_stopword |= 'stopword' in x

    return (not is_in_identities_in_dict) or is_stopword or custom_filter(o)


def get_isin_array(dictionary_data,obj_inds):
    isin_dict = []
    custom_filt = lambda x: x.postag == 'V'
    for i,o in enumerate(obj_inds):
        is_not_in_dict_or_is_stopword_or_verb = should_filter(o,dictionary_data, custom_filt)
        if is_not_in_dict_or_is_stopword_or_verb:
            isin_dict.append([1,0])
        else:
            isin_dict.append([0,1])

    return np.array(isin_dict)





def look_in_dict(dep_parses,dictionary=None, sets=None,set_names=None):

    feature_dict = {}
    for dep_objs in dep_parses:

        features = defaultdict(set)

        for i in range(len(dep_objs)):
            for j in range(min(2,len(dep_objs) - i)):
                dp_objs = dep_objs[i:(i+j+1)]
                dp_obj = dp_objs[0] if len(dp_objs) == 1 else DependencyParseObject().join(dp_objs)
                # Do dictionary lookups
                word_forms = get_wordforms_to_lookup(dp_obj)
                for w, val in word_forms.items():
                    in_dicts = set()
                    if w == '':
                        continue
                    if dictionary:
                        in_dicts = dictionary.GetDictVector(w)

                    if sets:
                        for s_ind, s in enumerate(sets):
                            if w in s:
                                in_dicts.add(set_names[s_ind])

                    for dictname in in_dicts:
                        for oid in dp_obj.all_original_ids:
                            if j ==0:
                                features[oid-1].add("in_dict:"+dictname)
                            else:
                                features[oid-1].add("n_gram:in_dictionary:"+dictname)

        feature_dict[dep_objs[0].tweet_id] = features
    return feature_dict
