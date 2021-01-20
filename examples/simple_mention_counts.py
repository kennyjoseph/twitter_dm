__author__ = 'mbenigni'

import pickle as pickle
import sys
from collections import Counter
from multiprocessing import Pool
from os import listdir, mkdir
import os
from twitter_dm.utility.general_utils import tab_stringify_newline as tsn, mkdir_no_err

if len(sys.argv) != 4:
    print('usage:  [input_dir] [output dir] [# cores for execution]')
    sys.exit(-1)


INPUT_DIR = sys.argv[1]
OUTPUT_DIR = sys.argv[2]
mkdir_no_err(OUTPUT_DIR)
def get_user_info(d):

    #i, uid = d
    #if i % 1000 == 0:
    #    print i
    #try:
        i, uid = d
        u = pickle.load(open(os.path.join(INPUT_DIR,'obj', uid), 'rb'))
        fname = os.path.join(INPUT_DIR,'json',uid + '.json.gz')

        u.populate_tweets_from_file(fname, store_json=False,
                                    do_arabic_stemming=False,
                                    do_parse_created_at=False,
                                    do_lemmatize=False,
                                    do_tokenize=False)

        of = open(os.path.join(OUTPUT_DIR,uid+".txt"),"w")
        mention_counter = Counter()
        for tw in u.tweets:
            ment_len = len(tw.mentions) if tw.mentions else 0
            mention_counter[ment_len] += 1
            if tw.mentions and len(tw.mentions) >= 3:
                of.write(tsn([tw.id,len(tw.mentions)]))
        of.close()
        return uid, mention_counter

    #except:
    #    return uid, Counter()


objfiles = listdir(os.path.join(INPUT_DIR,'obj/'))
jsonfiles = set([os.path.basename(f)[:-8] for f in listdir(os.path.join(INPUT_DIR,'json/'))])
print(list(jsonfiles)[:5])
print(objfiles[:5])
onlyfiles = [os.path.basename(o) for o in objfiles if o in jsonfiles]

print('N FILES: ', len(onlyfiles))
print(onlyfiles[:5])
#results = [get_user_info((0,onlyfiles[0]))]

pool = Pool(int(sys.argv[3]))
results = pool.map(get_user_info, enumerate(onlyfiles))
pool.close()
pool.terminate()

of = open(os.path.join(OUTPUT_DIR,"mention_counts_total.tsv"),"w")
for uid, mention_counter in results:
    for k,v in list(mention_counter.items()):
        of.write(tsn([uid,k,v]))
of.close()
