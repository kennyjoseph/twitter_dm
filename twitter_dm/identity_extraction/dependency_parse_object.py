__author__ = 'kennyjoseph'

import re
from ..nlp.nlp_helpers import *
from ..utility.tweet_utils import get_stopwords
from nltk.corpus import wordnet as wn
import sys

stopwords = get_stopwords()


class DependencyParseObject:
    def __init__(self, full_line=None, object_ids=[],  term_map=None, do_lemmatize=True, do_singular=True):
        self.cpostag = None
        self.features = []
        self.all_original_ids = []
        if full_line is not None:
            line = full_line.split("\t")
            self.line = line
            self.id = int(line[0])
            self.text = line[1]
            if line[2] != '_':
                self.lemma = line[2]
            self.postag = line[4]
            self.features = [x for x in line[5].split("|") if x != '' and x != '_']
            self.head = int(line[6])
            self.deprel = line[7]
            self.tweet_id = None
            self.dataset = None
            self.is_reply = None
            self.label = ''
            self.twitter_nlp_label = ''

            if len(line) == 8:
                pass
            elif len(line) == 9:
                self.label = line[8]
            elif len(line) == 11:
                self.tweet_id, self.dataset,self.is_reply = line[8:]
            elif len(line) == 12:
                self.tweet_id, self.dataset,self.is_reply,self.label = line[8:12]
            elif len(line) == 13:
                self.tweet_id, self.dataset, self.is_reply = line[10:13]
            elif len(line) == 14:
                self.tweet_id, self.dataset, self.is_reply, self.label = line[10:]
            elif len(line) == 15:
                self.tweet_id, self.dataset, self.is_reply, blah, self.label = line[10:]
            else:
                print 'UNRECOGNIZED FORMAT!!!!!!!!'
                print line
                sys.exit(-1)

            wn_pos = penn_to_wn(self.postag)
            cleaned_text = get_cleaned_text(self.text)
            self.lemma = lemmatize(cleaned_text, wn_pos)
            self.all_original_ids = [self.id]
            self.singular_form = cleaned_text
            if do_singular:
                self.singular_form = get_singular_fast(cleaned_text)


        elif len(object_ids):
            new_id = [obj_id for obj_id in object_ids if term_map[obj_id].head not in object_ids]
            if len(new_id) > 1:
                h = term_map[new_id[0]].head
                for x in new_id[1:]:
                    if term_map[x].head != h:
                        print 'new_id len > 1 and not same head'
                        assert False
                print 'warn: new_id len > 1, but all same head, randomly picking first'

            self.id = new_id[0]
            self.text = ' '.join([term_map[x].text for x in sorted(object_ids)])
            self.postag = ' '.join([term_map[x].postag for x in sorted(object_ids)])
            self.head = term_map[self.id].head
            self.deprel = ' '.join([term_map[x].deprel for x in sorted(object_ids)])
            self.lemma= ' '.join([term_map[x].lemma for x in sorted(object_ids)])
            label = 'O'
            for z in object_ids:
                if term_map[z].label == 'Identity':
                    label = 'Identity'
            self.label = label
            self.singular_form = ' '.join([term_map[x].singular_form for x in sorted(object_ids)])
            original_term_maps = [term_map[x].all_original_ids for x in object_ids]
            self.all_original_ids = [item for sublist in original_term_maps for item in sublist]

    def __str__(self):
        return " ".join([self.text, str(self.id), self.postag, self.label])

    def __unicode__(self):
        s = " ".join([unicode(x) for x in [self.id, self.head,self.text,self.postag,  self.label]])
        if self.deprel != "_":
            s += " " + self.deprel
        return s

    def get_super_conll_form(self):
        return "\t".join(unicode(x) for x in
                            [self.id,self.text,self.lemma,self.postag,self.postag,
                             '|'.join(self.features),self.head,self.deprel,'_','_',
                             self.tweet_id,self.dataset,self.is_reply,self.label])


    def get_pure_conll_form(self):
        ptb = [f for f in self.features if 'penn_treebank_pos=' in f]
        ptb_tag = '_' if not len(ptb) else ptb[1].replace("penn_treebank_pos=","")
        return "\t".join(unicode(x) for x in
                         [self.id,self.text,self.lemma,ptb_tag,ptb_tag,
                             '_',self.head,self.deprel,'_','_'])


    def word_features(self, is_prev_or_post):
        feats = []

        feats.append("word_low:" + self.text.lower())

        if self.deprel != "_":
            feats.append('DEPREL:' + self.deprel)

        feats.append('POS:' + self.postag)

        if(len(self.text) >= 3) and not is_prev_or_post:
            x = 0
            feats.append("prefix=%s" % self.text[0:1].lower())
            feats.append("prefix=%s" % self.text[0:2].lower())
            #feats.append("prefix=%s" % self.text[0:3].lower())
            feats.append("suffix=%s" % self.text[len(self.text)-1:len(self.text)].lower())
            feats.append("suffix=%s" % self.text[len(self.text)-2:len(self.text)].lower())
            #feats.append("suffix=%s" % self.text[len(self.text)-3:len(self.text)].lower())

        #if self.text[0] == '@':
        #    feats.append('@')
        if self.text[0] == '#':
            feats.append('HT')

        if re.search(r'^[A-Z]', self.text):
            feats.append('INITCAP')
        if re.match(r'^[A-Z]+$', self.text) and len(self.text) > 1:
            feats.append('ALLCAP')
        if re.match(r'.*[0-9].*', self.text):
            feats.append('HASDIGIT')
        if re.match(r'^[0-9]$', self.text):
            feats.append('SINGLEDIGIT')
        if re.match(r'^[0-9][0-9]$', self.text):
            feats.append('DOUBLEDIGIT')
        if re.match(r'.*-.*', self.text):
            feats.append('HASDASH')

        if is_prev_or_post:
            feats += [f for f in self.features if 'penn' in f]
        else:
            feats += self.features

        return feats


    def join(self, list_of_objs):
        """
        Creates a new dependency parse object from a list of dependency parse objs.
        SHOULD NOT BE USED WHEN CREATING THE OBJECTS ... only useful for, e.g.,
        doing text lookups in dictionaries
        :param list_of_objs: A list of DependencyParseObjects that will be combined
        :return: self, a new dependnecy parse object
        """
        self.id = None
        #elf.cpostag = " ".join([x.cpostag for x in list_of_objs])
        self.text = ' '.join([x.text for x in list_of_objs])
        self.postag = ' '.join([x.postag for x in list_of_objs])
        self.head = None
        self.deprel = ' '.join([x.deprel for x in list_of_objs])
        self.lemma = ' '.join([x.lemma for x in list_of_objs])
        self.label = ' '.join([x.label for x in list_of_objs])
        self.all_original_ids = [x.id for x in list_of_objs]
        self.features = [y for x in list_of_objs for y in x.features]
        self.dataset = list_of_objs[0].dataset
        self.is_reply = list_of_objs[0].is_reply
        self.singular_form = ' '.join([x.singular_form for x in list_of_objs])
        return self


NOUN_TAGS = set(['NN', 'NNS', 'NNP', 'NNPS','N','^','S','Z','M'])#,'O'
VERB_TAGS = set(['VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ','V','T'])
def is_noun(tag):
    return tag in NOUN_TAGS\
           or len(set(tag.split(" ")).intersection(NOUN_TAGS)) > 0


def is_verb(tag):
    return tag in VERB_TAGS or len(set(tag.split(" ")).intersection(VERB_TAGS)) > 0


def is_adverb(tag):
    return tag in ['RB', 'RBR', 'RBS','R']


def is_adjective(tag):
    return tag in ['JJ', 'JJR', 'JJS','A']

def is_prep_or_det(tag):
    return tag in ['P','D']

def is_possessive(tag):
    return tag == 'L'


def penn_to_wn(tag):
    if is_adjective(tag):
        return wn.ADJ
    elif is_noun(tag):
        return wn.NOUN
    elif is_adverb(tag):
        return wn.ADV
    elif is_verb(tag):
        return wn.VERB
    return None
