__author__ = 'kjoseph'
import itertools
import Queue
from collections import defaultdict

from dependency_parse_object import DependencyParseObject, is_noun, is_verb


def get_parse(dp_objs):
    term_map = {}

    map_to_head = defaultdict(list)
    for parse_object in dp_objs:
        if parse_object.head > 0:
            map_to_head[parse_object.head].append(parse_object.id)
        term_map[parse_object.id] = parse_object

    # first manually combine MWE
    mwe_to_combine = get_mwe_combinations(map_to_head,term_map)
    for mwe in mwe_to_combine:
        combine_terms(mwe,term_map,map_to_head)

    #conj_to_combine = get_conj_combinations(map_to_head,term_map)
    #for conj in conj_to_combine:
    #    combine_terms(conj,term_map,map_to_head)

    # now manually chunk the nouns together
    #nouns_to_combine = get_noun_combinations(map_to_head,term_map)
    #for noun_set in nouns_to_combine:
    #    combine_terms(noun_set,term_map, map_to_head)

    #verbs_to_combine = get_verb_combinations(map_to_head,term_map)
    #for verb_set in verbs_to_combine:
    #    combine_terms(verb_set,term_map, map_to_head)


    roots =[]
    non_terms = []
    for parse_object in term_map.values():
        if parse_object.head == 0:
            roots.append(parse_object)
        elif parse_object.head == -1:
            non_terms.append(parse_object)

    # now build the parse tree
    to_parse = Queue.LifoQueue()
    for root in reversed(roots):
        to_parse.put([root,0])

    return to_parse, term_map, map_to_head, non_terms



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


def get_verb_combinations(map_to_head,term_map):
    to_combine = []
    for head_id, children in map_to_head.iteritems():
        head = term_map[head_id]
        if len(children) == 0 or not is_verb(head.postag):
            continue

        for child_id in children:
            child = term_map[child_id]
            if is_verb(child.postag) and child.id == (head.id +1):
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
            if child.deprel == 'MWE':
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
            if len(d[0].intersection(d[1])) > 0:
                combination_found = True
                to_combine.append(set.union(d[0],d[1]))
                [to_combine.remove(x) for x in to_combine if x == d[0]]
                [to_combine.remove(x) for x in to_combine if x == d[1]]
                removed.append(d[0])
                removed.append(d[1])
    return to_combine

def combine_terms(noun_set,term_map, map_to_head):
    new_parse_obj = DependencyParseObject(object_ids=noun_set,term_map=term_map)
    # okay, we've created a new parse object
    # now we need to update the relations to it
    for id in noun_set:
        if id == new_parse_obj.id:
            term_map[id] = new_parse_obj

            if id in map_to_head:
                for child_id in noun_set:
                    if child_id in map_to_head[id]:
                        map_to_head[id].remove(child_id)
        else:
            # things dependent on this thing need to become dependent on the new parse object
            if id in map_to_head:
                for child in map_to_head[id]:
                    if child not in noun_set:
                        map_to_head[new_parse_obj.id].append(child)
                        term_map[child].head = new_parse_obj.id
                del map_to_head[id]
            del term_map[id]


def print_parse(parse_out, term_map, map_to_head):
    while not parse_out.empty():
        curr_head,level = parse_out.get()
        print " "*level  + "  " +  curr_head.__unicode__()
        for child in reversed(map_to_head.get(curr_head.id,[])):
            parse_out.put([term_map[child],level+1])


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


