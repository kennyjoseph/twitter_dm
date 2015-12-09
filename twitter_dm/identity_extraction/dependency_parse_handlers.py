__author__ = 'kjoseph'
import itertools
from collections import defaultdict, deque

from dependency_parse_object import DependencyParseObject, is_noun, is_verb
from util import get_wordforms_to_lookup


PEOPLE_TERMS_SET = {"people","person","persons","ppl","peeps",'member','members'}
NOT_TERMS_SET = {"never", "no","not"}

def process_dep_parse(dp_objs,
                      combine_mwe=True,
                      combine_determiners_and_verb_preps=False,
                      combine_conj=False,
                      combine_nouns=False,
                      combine_verbs=False,
                      combination_set=None,
                      combination_set_range=3,
                      combine_people_with_mod=False,
                      combine_not_with_parent=False):

    dp_objs = deepcopy(dp_objs)
    term_map = {}

    map_to_head = defaultdict(list)

    for parse_object in dp_objs:
        if parse_object.head > 0:
            map_to_head[parse_object.head].append(parse_object.id)
        term_map[parse_object.id] = parse_object

    if combination_set:
        dictionary_based_combine = get_dictionary_based_combinations(
                                            dp_objs,combination_set,combination_set_range)
        for d in dictionary_based_combine:
            combine_terms(d,term_map,map_to_head)

    # first manually combine MWE
    if combine_mwe:
        mwe_to_combine = get_mwe_combinations(map_to_head,term_map)
        for mwe in mwe_to_combine:
            combine_terms(mwe,term_map,map_to_head)

    if combine_people_with_mod:
        to_combine = get_people_combinations(map_to_head,term_map)
        for people_set in to_combine:
            combine_terms(people_set,term_map, map_to_head)

    if combine_not_with_parent:
        to_combine = get_not_combinations(map_to_head,term_map)
        for not_set in to_combine:
            combine_terms(not_set,term_map,map_to_head)

    if combine_verbs:
        verbs_to_combine = get_verb_combinations(map_to_head,term_map)
        for verb_set in verbs_to_combine:
            combine_terms(verb_set,term_map, map_to_head)


    if combine_conj:
        conj_to_combine = get_conj_combinations(map_to_head,term_map)
        for conj in conj_to_combine:
            combine_terms(conj,term_map,map_to_head)

    if combine_determiners_and_verb_preps:
        det_to_combine = get_determiner_combinations(map_to_head,term_map)
        for det in det_to_combine:
            combine_terms(det,term_map,map_to_head)

    if combine_nouns:
        nouns_to_combine = get_noun_combinations(map_to_head,term_map)
        for noun_set in nouns_to_combine:
            combine_terms(noun_set,term_map, map_to_head)



    roots =[]
    non_terms = []
    for parse_object in term_map.values():
        if parse_object.head == 0:
            roots.append(parse_object)
        elif parse_object.head == -1:
            non_terms.append(parse_object)

    # now build the parse tree
    parse_roots = deque()
    for root in reversed(roots):
        parse_roots.append([root,0])

    return parse_roots, term_map, map_to_head, non_terms


def get_dictionary_based_combinations(dp_objs,combination_set,combination_set_range):
    to_combine = []
    for i in range(len(dp_objs)):
        for j in range(1,min(combination_set_range,len(dp_objs) - i)):
            curr_objs = dp_objs[i:(i+j+1)]
            dp_obj = DependencyParseObject().join(curr_objs)
            # Do dictionary lookups
            word_forms = get_wordforms_to_lookup(dp_obj)
            for w, val in word_forms.items():
                if w in combination_set:
                    to_combine.append(set([x+1 for x in range(i, i+j+1)]))
    return get_combinations(to_combine)

def get_noun_combinations(map_to_head,term_map):
    to_combine = []
    for head_id, children in map_to_head.iteritems():
        head = term_map[head_id]
        if len(children) == 0 or not (is_noun(head.postag) or head.postag in ['D','@','A','R']) :
            continue

        for child_id in children:
            child = term_map[child_id]
            if is_noun(child.postag) or child.postag in ['D','@','A','R']:
                to_combine.append({child.id, head.id})

    return get_combinations(to_combine)

def get_people_combinations(map_to_head,term_map):
    to_combine = []
    for head_id, children in map_to_head.iteritems():
        head = term_map[head_id]
        if len(children) == 0 or head.text.lower() not in PEOPLE_TERMS_SET:
            continue

        for child_id in children:
            child = term_map[child_id]
            if is_noun(child.postag) or child.postag == 'A':
                to_combine.append({child.id, head.id})

    return get_combinations(to_combine)

def get_not_combinations(map_to_head,term_map):
    to_combine = []
    for head_id, children in map_to_head.iteritems():
        head = term_map[head_id]
        if len(children) == 0:
            continue

        for child_id in children:
            child = term_map[child_id]
            if child.text.lower() in NOT_TERMS_SET and abs(child.id - head.id) == 1:
                to_combine.append({child.id, head.id})

    return get_combinations(to_combine)


def get_determiner_combinations(map_to_head,term_map):
    to_combine = []
    for head_id, children in map_to_head.iteritems():
        head = term_map[head_id]

        for child_id in children:
            child = term_map[child_id]

            if (abs(child.id - max(head.all_original_ids))==1 or abs(child.id - min(head.all_original_ids))==1)\
                    and (('N' in head.postag and child.postag == 'D') or ('V' in head.postag and child.postag in ['P','R'])):
                to_combine.append({child.id, head.id})

    return get_combinations(to_combine)


def get_verb_combinations(map_to_head,term_map):
    to_combine = []
    for head_id, children in map_to_head.iteritems():
        head = term_map[head_id]
        if not is_verb(head.postag) and head.postag != 'P':
            continue

        for child_id in children:
            child = term_map[child_id]
            if abs(child.id -head.id) == 1 and (is_verb(child.postag) or child.postag=='P'):
                to_combine.append({child.id, head.id})

    return get_combinations(to_combine)


def get_mwe_combinations(map_to_head,term_map):
    to_combine = []
    for head_id, children in map_to_head.iteritems():
        head = term_map[head_id]
        if len(children) == 0:
            continue

        for child_id in children:
            child = term_map[child_id]
            if child.deprel == 'MWE' and abs(child.id - head.id)==1:
                to_combine.append({child.id, head.id})

    return get_combinations(to_combine)


def get_conj_combinations(map_to_head,term_map):
    to_combine = []
    for head_id, children in map_to_head.iteritems():
        head = term_map[head_id]
        if len(children) == 0:
            continue

        for child_id in children:
            child = term_map[child_id]
            if child.deprel == 'CONJ':
                to_combine.append({child.id, head.id})

    return get_combinations(to_combine)

def get_combinations(to_combine):
    combination_found = True
    while combination_found:
        combination_found = False
        combos = itertools.combinations(to_combine,2)
        removed = []
        for d in combos:
            if len([d[0] == r or d[1] == r for r in removed]):
                continue

            if d[0].issuperset(d[1]):
                [to_combine.remove(x) for x in to_combine if x == d[1]]
                removed.append(d[1])
            elif d[1].issuperset(d[0]):
                [to_combine.remove(x) for x in to_combine if x == d[0]]
                removed.append(d[0])
            elif len(d[0].intersection(d[1])) > 0:
                combination_found = True
                to_combine.append(set.union(d[0],d[1]))
                [to_combine.remove(x) for x in to_combine if x == d[0]]
                [to_combine.remove(x) for x in to_combine if x == d[1]]
                removed.append(d[0])
                removed.append(d[1])
    return to_combine

def combine_terms(term_set, term_map, map_to_head):
    new_parse_obj = DependencyParseObject(object_ids=term_set, term_map=term_map)
    # okay, we've created a new parse object
    # now we need to update the relations to it
    for id in term_set:
        if id == new_parse_obj.id:
            term_map[id] = new_parse_obj

            if id in map_to_head:
                for child_id in term_set:
                    if child_id in map_to_head[id]:
                        map_to_head[id].remove(child_id)
        else:
            # things dependent on this thing need to become dependent on the new parse object
            if id in map_to_head:
                for child in map_to_head[id]:
                    # have to ensure no cycles b/c of some weirdness when doing dictionary-based substitions
                    if child not in term_set and new_parse_obj.id not in map_to_head.get(child,[]):
                        map_to_head[new_parse_obj.id].append(child)
                        term_map[child].head = new_parse_obj.id
                del map_to_head[id]
            del term_map[id]

            # have to ensure that this node is updated as a child of other nodes
            for k, v in map_to_head.items():
                if id in v:
                    v.remove(id)
                    # ensure no cycles
                    if new_parse_obj.id not in v and new_parse_obj.id != k and\
                            k not in map_to_head.get(new_parse_obj.id,[]):
                        v.append(new_parse_obj.id)




from copy import deepcopy
def print_parse(parse_roots, term_map, map_to_head):
    parse_roots_copy = deepcopy(parse_roots)
    while len(parse_roots_copy):
        curr_head,level = parse_roots_copy.pop()
        print " "*level  + "  " +  curr_head.__unicode__()
        for child in reversed(map_to_head.get(curr_head.id,[])):
            parse_roots_copy.append([term_map[child],level+1])

def get_entities_from_parse(term_map):
    all_proper = []
    all_entities = []
    all_entities_original_ids = []
    all_proper_original_ids = []
    for k,v in term_map.iteritems():
        if is_noun(v.postag) or v.postag == '@' or v.postag == '#':
            text = []
            split_text = v.text.split()

            ent_ids = []
            for x in range(len(split_text)):
                t = split_text[x]#.strip(string.punctuation)
                #if x == 0 and t in stopwords:
                #    continue
                text.append(t)
                ent_ids.append(v.all_original_ids[x])

            if len(text) > 0 and v.postag != 'O':
                if '^' in v.postag and v.text[0].isupper():
                    all_proper.append(" ".join(text))
                    all_proper_original_ids.append(sorted(v.all_original_ids))

                all_entities.append(" ".join([t.lower() for t in text]))
                all_entities_original_ids.append(sorted(ent_ids))

    return all_entities, all_proper, all_entities_original_ids, all_proper_original_ids


